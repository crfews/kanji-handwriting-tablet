#### IMPORTS ###################################################################

import os
import datetime
from sqlalchemy import (
    ForeignKey,
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    Float,
    String,
    Date,
    Boolean,
    PickleType,
    insert,
    select,
    engine,
    UniqueConstraint,
    event)

#### CREATE DATABASE ENGINE ####################################################

_db_path = os.path.join(os.path.dirname(__file__), "db.sqlite3")
eng = create_engine(f"sqlite+pysqlite:///{_db_path}", echo=True)
#_engine = create_engine(f"sqlite+pysqlite:///:memory:", echo=True)
_metadata_obj = MetaData()

@event.listens_for(engine.Engine, "connect")
def _enable_foreign_keys(dbapi_con, con_record):
    dbapi_con.execute("PRAGMA foreign_keys=ON;")

#### TABLE DEFINITIONS #########################################################

card_types_table = Table(
    "card_types",
    _metadata_obj,
    Column("id",
           Integer,
           primary_key=True,
           nullable=False),
    Column("name",
           String,
           nullable=False),
)


field_type_table = Table(
    "field_types",
    _metadata_obj,
    Column("id",
           Integer,
           primary_key=True,
           nullable=False),
    Column("card_type_id", ForeignKey("card_types.id", ondelete="CASCADE"), nullable=False),
    Column("name",
           String,
           nullable=False),
    Column("is_text",
           Boolean,
           nullable=False),
    Column("is_number",
           Boolean,
           nullable=False),
    Column("is_pickle",
           Boolean,
           nullable=False),
    UniqueConstraint("card_type_id", "name", name="uix_field_types_card_type_name")
)


cards_table = Table(
    "cards",
    _metadata_obj,
    Column("id",
           Integer,
           primary_key=True,
           nullable=False),
    Column("study_id",
           Integer,
           unique=True,
           nullable=False),
    Column("type_id",
           ForeignKey("card_types.id", ondelete="CASCADE"),
           nullable=False),
    Column("studied",
           Boolean,
           nullable=False),
    Column("due_date_increment",
           Integer,
           nullable=False),
    Column("due_date",
           Date,
           nullable=False),
)


card_fields_table = Table(
    "card_fields",
    _metadata_obj,
    Column("id",
           Integer,
           primary_key=True,
           nullable=False),
    Column("card_id",
           ForeignKey("cards.id", ondelete="CASCADE"),
           nullable=False),
    Column("field_type_id",
           ForeignKey("field_types.id", ondelete="CASCADE"),
           nullable=False),
    Column("text_field",
           String,
           nullable=True),
    Column("number_field",
           Float,
           nullable=True),
    Column("pickle_field",
           PickleType,
           nullable=True),
)

#### PUBLIC METHODS ############################################################

def add_card_type(name: str) -> int:
    """Create a new card type and return its ID."""
    with eng.begin() as conn:
        result = conn.execute(
            insert(card_types_table)
            .returning(card_types_table.c.id)
            .values(name=name)
        )
        return result.scalar_one()


def add_field_type(card_type_id: int,
                   name: str,
                   is_text: bool,
                   is_int: bool,
                   is_pickle: bool) -> int:
    """Create a field type belonging to a card type."""

    assert (is_text or is_int or is_pickle)
    if is_text:
        assert (not (is_int or is_pickle))
    elif is_int:
        assert (not (is_text or is_pickle))
    elif is_pickle:
        assert (not (is_int or is_text))
        
        
    with eng.begin() as conn:
        result = conn.execute(
            insert(field_type_table)
            .returning(field_type_table.c.id)
            .values(
                card_type_id=card_type_id,
                name=name,
                is_text=is_text,
                is_int=is_int,
                is_pickle=is_pickle
            )
        )
        return result.scalar_one()


def add_card(type_id: int,
             study_id: int,
             studied: bool=False,
             due_date_increment: int=0,
             due_date: datetime.date=datetime.date.max) -> int:
    """Create a new card of a given type."""
    with eng.begin() as conn:
        result = conn.execute(
            insert(cards_table)
            .returning(cards_table.c.id)
            .values(
                type_id=type_id,
                study_id=study_id,
                studied=studied,
                due_date_increment=due_date_increment,
                due_date=due_date
            )
        )
        return result.scalar_one()


def add_card_field(card_id: int,
                   field_type_id: int,
                   text_field=None,
                   int_field=None,
                   pickle_field=None) -> int:
    """Add a field to a card, selecting the correct field encoding."""
    with eng.begin() as conn:
        result = conn.execute(
            insert(card_fields_table)
            .returning(card_fields_table.c.id)
            .values(
                card_id=card_id,
                field_type_id=field_type_id,
                text_field=text_field,
                int_field=int_field,
                pickle_field=pickle_field
            )
        )
        return result.scalar_one()



def get_card_with_fields(card_id: int):
    with eng.begin() as conn:

        # 1. Fetch the card itself
        card_row = conn.execute(
            select(cards_table).where(cards_table.c.id == card_id)
        ).fetchone()

        if card_row is None:
            return None  # card does not exist

        # 2. Fetch the card fields joined with their field type metadata
        field_rows = conn.execute(
            select(
                card_fields_table.c.text_field,
                card_fields_table.c.int_field,
                card_fields_table.c.pickle_field,
                field_type_table.c.name,
                field_type_table.c.is_text,
                field_type_table.c.is_int,
                field_type_table.c.is_pickle,
            ).select_from(
                card_fields_table.join(
                    field_type_table,
                    card_fields_table.c.field_type_id == field_type_table.c.id
                )
            ).where(
                card_fields_table.c.card_id == card_id
            )
        ).fetchall()

        # 3. Convert database row values into a neat dictionary
        fields = {}
        for row in field_rows:
            if row.is_text:
                fields[row.name] = row.text_field
            elif row.is_int:
                fields[row.name] = row.int_field
            elif row.is_pickle:
                fields[row.name] = row.pickle_field
            else:
                fields[row.name] = None

        # 4. Return structured response
        return {
            "id": card_row.id,
            "study_id": card_row.study_id,
            "type_id": card_row.type_id,
            "studied": card_row.studied,
            "due_date_increment": card_row.due_date_increment,
            "due_date": card_row.due_date,
            "fields": fields,
        }


def get_all_card_types_with_field_types():
    """
    Returns all card types and their field types in the form:
    {
        card_type_name: {
            field_type_name: {
                "is_text": bool,
                "is_int": bool,
                "is_pickle": bool
            },
            ...
        },
        ...
    }
    """
    with eng.begin() as conn:
        # Step 1: Fetch all card types
        card_types = conn.execute(
            select(card_types_table.c.id, card_types_table.c.name)
        ).fetchall()

        # Prepare return structure
        result = {card_type.name: {} for card_type in card_types}

        # Step 2: Fetch all field types joined with their card type
        field_types = conn.execute(
            select(
                field_type_table.c.card_type_id,
                field_type_table.c.name,
                field_type_table.c.is_text,
                field_type_table.c.is_int,
                field_type_table.c.is_pickle,
            )
        ).fetchall()

        # Step 3: Fill in dictionary
        for ft in field_types:
            # Find which card type this belongs to
            card_type_name = next(ct.name for ct in card_types if ct.id == ft.card_type_id)

            result[card_type_name][ft.name] = {
                "is_text": ft.is_text,
                "is_int": ft.is_int,
                "is_pickle": ft.is_pickle
            }

        return result


#### MODULE FOOTER #############################################################

# Initialize the database
_metadata_obj.create_all(eng)
#_initialize_defaults()









# def _initialize_defaults():
#     with eng.begin() as conn:

#         defaults = {
#             # field_name: is_text | is_int | is_pickle

#             "Character": [
#                 ("char",               True,  False, False),
#                 ("stroke count",       False, True,  False),
#                 ("raw strokes",        False, False, True),
#                 ("processed strokes",  False, False, True),
#                 ("meaning",            True,  False, False),
#                 ("romaji",             True,  False, False),
#                 ("onyomi",             True,  False, False),
#             ],
#             "Word": [
#                 ("writings",           True,  False,  False),
#                 ("grammar",            True,  False,  False),
#                 ("kana writing",       True,  False,  False),
#                 ("meaning",            True,  False,  False),
#             ],

#         }

#         for card_type_name, field_specs in defaults.items():

#             # Check if the card type already exists
#             existing = conn.execute(
#                 select(card_types_table.c.id).where(
#                     card_types_table.c.name == card_type_name
#                 )
#             ).fetchone()

#             # Insert new card type if missing
#             if existing is None:
#                 result = conn.execute(
#                     insert(card_types_table)
#                     .returning(card_types_table.c.id)
#                     .values(name=card_type_name)
#                 )
#                 card_type_id = result.scalar_one()
#             else:
#                 card_type_id = existing.id

#             # Insert each field type *only if it does not already exist*
#             for name, is_text, is_int, is_pickle in field_specs:
#                 existing_field = conn.execute(
#                     select(field_type_table.c.id).where(
#                         (field_type_table.c.card_type_id == card_type_id) &
#                         (field_type_table.c.name == name)
#                     )
#                 ).fetchone()

#                 if existing_field is None:
#                     conn.execute(
#                         insert(field_type_table).values(
#                             card_type_id=card_type_id,
#                             name=name,
#                             is_text=is_text,
#                             is_int=is_int,
#                             is_pickle=is_pickle
#                         )
#                     )
