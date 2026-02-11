from typing import Iterator
import sqlalchemy as sqla
from datetime import date
from .database import *
from .kana_card import KanaCard
from .kanji_card import KanjiCard
from .phrase_card import PhraseCard

def query_learnable_card_ids(con: sqla.Connection | None = None) -> Iterator[int]:
    '''Returns a list of card ids where each card represents a card that has not been
    studied and has no unlearned prerequisites'''
    A = card_table
    R = card_relation_table
    B = card_table.alias('B')
    has_unlearned_prereq = sqla.exists(
        sqla.select(1)
        .select_from(R.join(B, R.c.card_b_id == B.c.id))
        .where(R.c.b_is_prereq == True)
        .where(R.c.card_a_id == A.c.id)
        .where(B.c.study_id <= 1))

    q = sqla.select(A.c.id)\
             .where(A.c.study_id < 1)\
             .where(~has_unlearned_prereq)

    with maybe_connection(con) as con:
        result = con.execute(q)
        for r in result:
            yield r[0]

def query_reviewable_card_ids(con: sqla.Connection | None = None) -> Iterator[int]:
    '''Returns a list of card ids where each card represents a card that has
    has been studied and has a due date before or equal too today'''

    q = sqla.select(card_table.c.id)\
            .where(card_table.c.study_id > 0)\
            .where(card_table.c.due_date <= date.today())

    with maybe_connection(con) as con:
        for r in con.execute(q):
            yield r[0]
        
def query_learnable_kana_cards(con: sqla.Connection | None = None) -> Iterator[KanaCard]:
    '''Returns a list of kana card objects where each card represents a card that has
    not been studied and has no unlearned prerequisites'''
    for c_id in query_learnable_card_ids(con):
        knc = KanaCard.by_card_id(c_id)
        if knc:
            yield knc

def query_reviewable_kana_card(con: sqla.Connection | None = None) -> Iterator[KanaCard]:
    '''Returns a list of kana card objects where each card has been learned and has
    a due date before or equal to today'''
    for c_id in query_reviewable_card_ids(con):
        knc = KanaCard.by_card_id(c_id)
        if knc:
            yield knc

def query_learnable_kanji_cards(con: sqla.Connection | None = None) -> Iterator[KanjiCard]:
    '''Returns a list of kanji card objects where each card represents a card that has
    not been studied and has no unlearned prerequisites'''
    for c_id in query_learnable_card_ids(con):
        kjc = KanjiCard.by_card_id(c_id)
        if kjc:
            yield kjc

def query_reviewable_kanji_cards(con: sqla.Connection | None = None) -> Iterator[KanjiCard]:
    '''Returns a list of kanji card objects where each card has been learned and has
    a due date before or equal to today'''
    for c_id in query_reviewable_card_ids(con):
        kjc = KanjiCard.by_card_id(c_id)
        if kjc:
            yield kjc


def query_learnable_phrase_cards(con: sqla.Connection | None = None) -> Iterator[PhraseCard]:
    '''Returns a list of phrase card objects where each card represents a card
    that has not been studied and has no unlearned prerequisites'''
    for c_id in query_learnable_card_ids(con):
        pc = PhraseCard.by_card_id(c_id)
        if pc:
            yield pc

def query_reviewable_phrase_cards(con: sqla.Connection | None = None) -> Iterator[PhraseCard]:
    '''Returns a list of phrase card objects where each card has been learned and
    has a due date before or equal to today'''
    for c_id in query_reviewable_card_ids(con):
        pc = PhraseCard.by_card_id(c_id)
        if pc:
            yield pc
