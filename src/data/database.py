# Author: Phillip Graham
# Description: Defines a database using sqlite containing tables for cards,
#     kana, kanji, phrases
# Last Modified: Wed. Feb. 11, 2026


################################################################################
# Imports
################################################################################

# Allows me to make recursively defined classes with pyright
from __future__ import annotations
import os
import sqlalchemy as sqla
from sqlalchemy import event
from contextlib import contextmanager

################################################################################
# Globals
################################################################################

KANA_CARD_KIND = 'kana'
KANJI_CARD_KIND = 'kanji'
PHRASE_CARD_KIND = 'phrase'

################################################################################
# Database Objects
################################################################################

_db_path = os.path.join(os.path.dirname(__file__), "db.sqlite3")
_engine = sqla.create_engine(f'sqlite+pysqlite:///{_db_path}', echo=True)
_metadata = sqla.MetaData()

@event.listens_for(sqla.engine.Engine, "connect")
def enable_foreign_keys(dbapi_con, con_record):
    dbapi_con.execute("PRAGMA foreign_keys=ON;")

drawing_table = sqla.Table(
    'drawings',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('stroke_count', sqla.Integer, unique=False, nullable=False),
    sqla.Column('strokes', sqla.PickleType, unique=False, nullable=False),
    sqla.Column('glyph', sqla.String, unique=False, nullable=True),
    sqla.Index('ix_drawings_stroke_count', 'stroke_count'))

card_table = sqla.Table(
    'cards',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('study_id', sqla.Integer, unique=False),
    sqla.Column("due_date_increment", sqla.Integer, nullable=False),
    sqla.Column('due_date', sqla.Date, nullable=False),
    sqla.Column('tags', sqla.String, nullable=True),
    sqla.Column('kind', sqla.String, nullable=True),
    sqla.Index('ix_cards_study_id', 'study_id'))

card_relation_table = sqla.Table(
    'card_relation',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('card_a_id', sqla.Integer, sqla.ForeignKey('cards.id'), nullable=False),
    sqla.Column('card_b_id', sqla.Integer, sqla.ForeignKey('cards.id'), nullable=False),
    sqla.Column('b_is_prereq', sqla.Boolean, nullable=False),
    sqla.Column('easily_confused', sqla.Boolean, nullable=False),
    sqla.Index("ix_card_rel_a", "card_a_id"),
    sqla.Index("ix_card_rel_b", "card_b_id"),)

kana_card_table = sqla.Table(
    'kana_cards',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('card_id', sqla.Integer, sqla.ForeignKey('cards.id'), unique=True, nullable=False),
    sqla.Column('drawing_id', sqla.Integer, sqla.ForeignKey('drawings.id'), nullable=True),
    sqla.Column('kana', sqla.String, unique=True, nullable=False),
    sqla.Column('romaji', sqla.String, unique=False, nullable=True),
    sqla.Index('ix_kana_cards_card_id', 'card_id'))

kanji_card_table = sqla.Table(
    'kanji_cards',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('card_id', sqla.Integer, sqla.ForeignKey('cards.id'), unique=True, nullable=False),
    sqla.Column('drawing_id', sqla.Integer, sqla.ForeignKey('drawings.id'), nullable=True),
    sqla.Column('kanji', sqla.String, unique=True, nullable=False),
    sqla.Column('on_yomi', sqla.String, unique=False, nullable=True),
    sqla.Column('kun_yomi', sqla.String, unique=False, nullable=True),
    sqla.Column('meaning', sqla.String, unique=False, nullable=True),
    sqla.Index('ix_kanji_cards_card_id', 'card_id'))

phrase_card_table = sqla.Table(
    'phrase_cards',
    _metadata,
    sqla.Column('id', sqla.Integer, primary_key=True, nullable=False),
    sqla.Column('card_id', sqla.Integer, sqla.ForeignKey('cards.id'), unique=True, nullable=False),
    sqla.Column('kanji_phrase', sqla.String, nullable=True),
    sqla.Column('kana_phrase', sqla.String, nullable=True),
    sqla.Column('meaning', sqla.String, nullable=False),
    sqla.Column('grammar', sqla.String, nullable=True),
    sqla.Index('ix_phrase_cards_card_id', 'card_id'))

# Construct the database
_metadata.create_all(_engine)

################################################################################
# Helper Functions
################################################################################

@contextmanager
def maybe_connection(con: sqla.Connection | None):
    '''Function used for 'where' clauses where the caller may want to reuse a
    pre-existing connection.'''
    owns_con = con is None
    if owns_con:
        con = _engine.connect()
    try:
        yield con
    finally:
        if owns_con:
            con.close()


@contextmanager
def maybe_connection_commit(con: sqla.Connection | None):
    '''Function used for 'where' clauses where the caller may want to reuse a
    pre-existing connection. Will always commit if it owns the connection.'''
    owns_con = con is None
    if owns_con:
        con = _engine.connect()
    try:
        yield con
    except Exception:
        if owns_con:
            con.rollback()
        raise
    else:
        if owns_con:
            con.commit()
    finally:
        if owns_con:
            con.close()
