import datetime
import database as db
import sqlalchemy as sqa
from typing import final
from collections.abc import Generator

# pyright: basic

########################################################################################################################
#### Field Type ########################################################################################################
########################################################################################################################

class FieldType:
    _id: int
    _name: str
    _is_text: bool
    _is_number: bool
    _is_pickle: bool
    _owning_card_type: 'CardType | None'

    #### Constructor ###################################################################################################

    def __init__(self,
                 id: int,
                 name: str,
                 is_text: bool,
                 is_number: bool,
                 is_pickle: bool,
                 owning_card_type: 'CardType'):
        self._id = id
        self._name = name
        self._is_text = is_text
        self._is_number = is_number
        self._is_pickle = is_pickle
        self._owning_card_type = owning_card_type

    #### Properties ####################################################################################################

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_text(self) -> bool:
        return self._is_text

    @property
    def is_number(self) -> bool:
        return self._is_number

    @property
    def is_pickle(self) -> bool:
        return self._is_pickle

    #### Methods #######################################################################################################

    def sync(self) -> None:
        """Insert or update this FieldType in the database."""
        if self._id < 1:
            with db.eng.begin() as conn:
                result = conn.execute(
                    sqa.insert(db.field_type_table)
                    .returning(db.field_type_table.c.id)
                    .values(
                        card_type_id=self._owning_card_type.id, # pyright: ignore
                        name=self._name,
                        is_text=self._is_text,
                        is_number=self._is_number,
                        is_pickle=self._is_pickle,
                    )
                )
                self._id = int(result.scalar_one())
        else:
            with db.eng.begin() as conn:
                conn.execute(
                    sqa.update(db.field_type_table)
                    .where(db.field_type_table.c.id == self._id)
                    .values(
                        name=self._name,
                        is_text=self._is_text,
                        is_number=self._is_number,
                        is_pickle=self._is_pickle,
                    )
                ) # pyright: ignore[reportAny]
        self._synced = True  # pyright: ignore[reportPrivateUsage]

        

########################################################################################################################
#### Field #############################################################################################################
########################################################################################################################

class Field:
    _id: int
    _name: str
    _is_text: bool
    _is_number: bool
    _is_pickle: bool
    _owning_card: 'Card | None'
    
    _synced: bool = False

    #### Constructor ###################################################################################################

    def __init__(self,
                 id: int,
                 name: str,
                 is_text: bool=False,
                 is_number: bool=False,
                 is_pickle: bool=False,
                 owning_card: 'Card | None'=None):
        self._id = id
        self._name = name
        self._is_text = is_text
        self._is_number = is_number
        self._is_pickle = is_pickle
        self._owning_card = owning_card
        
        if id > 0:
            self._synced = True
        else:
            self._synced = False

    #### Properties ####################################################################################################

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def owning_card(self) -> 'Card | None':
        return self._owning_card

    @property
    def synced(self) -> bool:
        return self._synced

    def _db_value_tuple(self) -> tuple[str | None, float | None, list[list[float]] | None]:
        """Implemented by subclasses: return (text, int, pickle)."""
        raise NotImplementedError

    def sync(self) -> None:
        """Insert/update this field in the DB."""
        if self._owning_card is None:
            raise RuntimeError("Cannot sync Field without owning Card.")

        # Find field_type
        field_type = None
        for ft in self._owning_card.card_type.field_types:
            if ft.name == self._name:
                field_type = ft
                break
        if field_type is None:
            raise ValueError(f"FieldType for '{self._name}' not found")

        text_val, int_val, pickle_val = self._db_value_tuple()

        if self._id < 1:
            # INSERT
            with db.eng.begin() as conn:
                result = conn.execute(
                    sqa.insert(db.card_fields_table)
                    .returning(db.card_fields_table.c.id)
                    .values(
                        card_id=self._owning_card.id,
                        field_type_id=field_type.id,
                        text_field=text_val,
                        number_field=int_val,
                        pickle_field=pickle_val,
                    )
                )
                self._id = int(result.scalar_one())  # pyright: ignore[reportPrivateUsage]
        else:
            # UPDATE
            with db.eng.begin() as conn:
                conn.execute(
                    sqa.update(db.card_fields_table)
                    .where(db.card_fields_table.c.id == self._id)
                    .values(
                        text_field=text_val,
                        number_field=int_val,
                        pickle_field=pickle_val,
                    )
                )

        self._synced = True  # pyright: ignore[reportPrivateUsage]

@final
class TextField(Field):
    _value: str

    def __init__(self, value: str, id: int, name: str, owning_card: 'Card | None'):
        super().__init__(id, name, True, False, False, owning_card=owning_card)
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def update_value(self, v: str):
        if v != self._value:
            self._synced = False
            self._value = v

    def _db_value_tuple(self):
        return self._value, None, None

 
@final
class NumberField(Field):
    _value: float

    def __init__(self, value: float, id: int, name: str, owning_card: 'Card | None'):
        super().__init__(id, name, False, True, False, owning_card=owning_card)
        self._value = value

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def update_value(self, v: float):
        if v != self._value:
            self._synced = False
            self._value = v

    def _db_value_tuple(self):
        return None, int(self._value), None


@final
class StrokeField(Field):
    _value: list[list[float]]

    def __init__(self, value: list[list[float]], id: int, name: str, owning_card: 'Card | None'):
        super().__init__(id, name, False, False, True, owning_card=owning_card)
        self._value = value

    @property
    def value(self) -> list[list[float]]:
        return self._value

    @value.setter
    def update_value(self, v: list[list[float]]):
        if v != self._value:
            self._synced = False
            self._value = v

    def _db_value_tuple(self):
        return None, None, self._value

    

########################################################################################################################
#### Card Type #########################################################################################################
########################################################################################################################
   
class CardType:
    _id: int
    _name: str
    _owned_field_types: list[FieldType]
    _synced: bool = False

    #### Constructor ###################################################################################################

    def __init__(self, id: int, name: str):
        self._id = id
        self._name = name
        self._owned_field_types = []

        if id > 0:
            self._synced = True
            stmnt = sqa.select(db.field_type_table)
            stmnt = stmnt.where(db.field_type_table.c.card_type_id == self.id)
            with db.eng.connect() as conn:
                res = conn.execute(stmnt)
                self._owned_field_types = [FieldType(r[0], r[2], r[3], r[4], r[5], self) for r in res] # pyright: ignore[reportAny]

    #### Properties ####################################################################################################

    @property
    def id(self) -> int:
        return self._id


    @property
    def name(self) -> str:
        return self._name


    @property
    def field_types(self) -> list[FieldType]:
        return self._owned_field_types
        
    #### Methods #######################################################################################################

    def get_instances(self) -> Generator['Card']:
        stmnt = sqa.select(db.cards_table)
        stmnt = stmnt.where(db.cards_table.c.type_id == self._id)
        with db.eng.connect() as conn:
            for row in conn.execute(stmnt):
                c = Card(row[0], row[1], row[3], row[4], row[5], self) # pyright: ignore[reportAny]
                yield c

    def add_instance(self) -> 'Card':
        max_study_id = 1
        with db.eng.begin() as conn:
            stmt = sqa.select(sqa.func.max(db.cards_table.c.study_id))
            result = conn.execute(stmt).scalar_one_or_none()
            if result:
                max_study_id = int(result) # pyright: ignore[reportAny]
        return Card(-1, max_study_id, False, 0, datetime.date.today(), owning_card_type=self) 
        
    def add_text_field(self, name: str) -> FieldType:
        if name in [ft.name for ft in self._owned_field_types]:
            raise ValueError(f"Field of name '{name}' already exists")
        ft = FieldType(-1, name, True, False, False, self)
        self._owned_field_types.append(ft)
        self._synced = False
        return ft

    def add_number_field(self, name: str) -> FieldType:
        if name in [ft.name for ft in self._owned_field_types]:
            raise ValueError(f"Field of name '{name}' already exists")
        ft = FieldType(-1, name, False, True, False, self)
        self._owned_field_types.append(ft)
        self._synced = False
        return ft

    def add_pickle_field(self, name: str) -> FieldType:
        if name in [ft.name for ft in self._owned_field_types]:
            raise ValueError(f"Field of name '{name}' already exists")
        ft = FieldType(-1, name, False, False, True, self)
        self._owned_field_types.append(ft)
        self._synced = False
        return ft

    def sync(self) -> None:
        """Insert/update this CardType and its FieldTypes."""
        if self._id < 1:
            with db.eng.begin() as conn:
                result = conn.execute(
                    sqa.insert(db.card_types_table)
                    .returning(db.card_types_table.c.id)
                    .values(name=self._name)
                )
                self._id = int(result.scalar_one())  # pyright: ignore[reportPrivateUsage]
        else:
            with db.eng.begin() as conn:
                conn.execute(
                    sqa.update(db.card_types_table)
                    .where(db.card_types_table.c.id == self._id)
                    .values(name=self._name)
                )

        self._synced = True  # pyright: ignore[reportPrivateUsage]

        # Sync all fields types we own
        for ft in self._owned_field_types:
            ft.sync()

########################################################################################################################
#### Card ##############################################################################################################
########################################################################################################################

class Card():
    _id: int
    _study_id: int
    _owning_card_type: CardType
    _owned_fields: dict[str, Field]
    _studied: bool
    _due_date_increment: int
    _due_date: datetime.date
    _synced: bool = False

    #### Constructor ###################################################################################################

    def __init__(self,
                 id: int,
                 study_id: int,
                 studied: bool,
                 due_date_increment: int,
                 due_date: datetime.date,
                 owning_card_type: CardType):
        self._id = id
        self._study_id = study_id
        self._studied = studied
        self._owning_card_type = owning_card_type
        self._owned_fields = {}
        self._due_date_increment = due_date_increment
        self._due_date = due_date

        # If the id is less than one than this does not yet exist in the database
        if id >= 1:
            self._synced = True

    ####################################################################################################################
    #### Properties ####################################################################################################
    ####################################################################################################################

    @property
    def id(self) -> int:
        return self._id

    @property
    def study_id(self) -> int:
        return self._study_id

    @property
    def due_date(self) -> datetime.date:
        return self._due_date

    @property
    def studied(self) -> bool:
        return self._studied
    
    @property
    def due_date_increment(self) -> int:
        return self._due_date_increment

    @property
    def card_type(self) -> CardType:
        """Returns the card type that this card belongs to"""
        return self._owning_card_type

    def update_due_date(self, date: datetime.date):
        self._synced = False
        self._due_date = date

    def update_due_date_increment(self, increment: int):
        self._synced = False
        self._due_date_increment = increment

    def update_studied(self, studied: bool):
        self._synced = False
        self._studied = studied
     
    def __getitem__(self, key: str) -> Field:
        """Searches against the fields of a card to return this card's instance of the field"""
        if key in self._owned_fields:
            return self._owned_fields[key]

        # Only allow access to fields for which a field type is defined
        field_type = None
        ftypes = self._owning_card_type.field_types
        for ft in ftypes:
            if ft.name == key:
                field_type = ft
                break
        if field_type is None:
            raise ValueError("No such field defined")

        # Search the database and see if a field of this type already exists
        # If the field already existed construct a field object to return
        row = None
        if self._id >= 1:
            stmnt = sqa.select(db.card_fields_table)
            stmnt = stmnt.where(db.card_fields_table.c.card_id == self.id and db.card_fields_table.c.field_type_id == field_type.id)
            with db.eng.connect() as conn:
                res = conn.execute(stmnt)
                row = res.one_or_none()
        if row:
            if field_type.is_number:
                f = NumberField(row[4], row[0], field_type.name, owning_card=self) # pyright: ignore[reportAny]
            elif field_type.is_text:
                f = TextField(row[3], row[0], field_type.name, owning_card=self) # pyright: ignore[reportAny]
            elif field_type.is_pickle:
                f = StrokeField(row[5], row[0], field_type.name, owning_card=self) # pyright: ignore[reportAny]
            else:
                raise ValueError(f"Field type '{field_type.name}' has no specified type")
            self._owned_fields[key] = f
            return f

        # If the field has not yet been created return a empty one that is marked as unsynced and mark the card as unsynced
        if field_type.is_number:
            f = NumberField(0, -1, field_type.name, owning_card=self)
        elif field_type.is_text:
            f = TextField('', -1, field_type.name, owning_card=self)
        elif field_type.is_pickle:
            f = StrokeField([], -1, field_type.name, owning_card=self)
        else:
            raise ValueError(f"Field type '{field_type.name}' has no specified type")

        self._owned_fields[key] = f
        self._synced = False
        return f
    
    def sync(self) -> None:
        """Insert or update this Card and its Field objects."""
        if self._id < 1:
            # INSERT
            with db.eng.begin() as conn:
                result = conn.execute(
                    sqa.insert(db.cards_table)
                    .returning(db.cards_table.c.id)
                    .values(
                        type_id=self._owning_card_type.id,
                        study_id=self._study_id,
                        studied=self._studied,
                        due_date_increment=self._due_date_increment,
                        due_date=self._due_date,
                    )
                )
                self._id = int(result.scalar_one())  # pyright: ignore[reportPrivateUsage]
        else:
            # UPDATE
            with db.eng.begin() as conn:
                conn.execute(
                    sqa.update(db.cards_table)
                    .where(db.cards_table.c.id == self._id)
                    .values(
                        study_id=self._study_id,
                        studied=self._studied,
                        due_date_increment=self._due_date_increment,
                        due_date=self._due_date,
                    )
                )

        self._synced = True  # pyright: ignore[reportPrivateUsage]

        # Sync fields
        for f in self._owned_fields.values():
            if not f.synced:
                f.sync()

    

#### PUBLIC FUNCTIONS ##########################################################


def get_all_card_types() -> Generator[CardType]:
    stmnt = sqa.select(db.card_types_table)

    with db.eng.connect() as conn:
        for row in conn.execute(stmnt):
            ct = CardType(int(row[0]), row[1]) # pyright: ignore[reportAny]
            yield ct

