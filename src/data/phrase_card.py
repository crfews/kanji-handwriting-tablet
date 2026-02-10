# Author: Phillip Graham
# Description: Defines a class used to wrap the phrase card table in the database
# Last Modified: Sun. Feb. 08, 2026

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from .database import phrase_card_table, maybe_connection, maybe_connection_commit
from .card import Card
from .helpers import is_kana, is_kanji
from .kana_card import KanaCard
from .kanji_card import KanjiCard

################################################################################
# class Definition
################################################################################

class PhraseCard:
    # Class Variables ##########################################################

    _id_cache: dict[int, PhraseCard] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _add_to_cache(cls, pc: PhraseCard):
        assert pc._db_id not in cls._id_cache
        cls._id_cache[pc._db_id] = pc

    @classmethod
    def _remove_from_cache(cls, pc: PhraseCard):
        del cls._id_cache[pc._db_id]


    @classmethod
    def _create_from_mapping(cls, m: Mapping, con: sqla.Connection | None = None) -> PhraseCard:
        db_id = int(m['id'])

        # Guard from duplication
        if db_id in cls._id_cache:
            return cls._id_cache[db_id]

        # Get the card from the database
        card_id = int(m['card_id'])
        card = Card.by_id(card_id, con=con)

        if card is None:
            raise ValueError(f'(Could not identify card of id: {card_id}')

        # Instantiate and cache
        obj = PhraseCard(
            db_id,
            card,
            m['kanji_phrase'],
            m['kana_phrase'],
            m['meaning'],
            m['grammar'],
            True)
        cls._add_to_cache(obj)

        return obj


    @classmethod
    def create(cls,
               meaning: str,
               grammar: str | None = None,
               kanji_phrase: str | None = None,
               kana_phrase: str | None = None,
               require_relationship = True) -> PhraseCard:
        # Check parameters
        if kanji_phrase == '':
            kanji_phrase = None
        if kana_phrase == '':
            kana_phrase = None
            
        if kanji_phrase is None and kana_phrase is None:
            raise ValueError('Invalid kanji phrase and kana phrase: both cannot be None')
        elif meaning is None or meaning == '':
            raise ValueError('Invalid meaning: cannot be null or empty')
        elif grammar == '':
            raise ValueError('Invalid grammar: cannot be empty string')

        if kana_phrase:
            contains_kana = False
            for c in kana_phrase:
                if not contains_kana and is_kana(c):
                    contains_kana = True
                if is_kanji(c):
                    raise ValueError(f"Invalid kana phrase: contains kanji '{c}'")
            if not contains_kana:
                raise ValueError('Invalid kana phrase: contains no kana')

        if kanji_phrase:
            contains_kanji = False
            for c in kanji_phrase:
                if is_kanji(c):
                    contains_kanji = True
                    break
            if not contains_kanji:
                raise ValueError('Invalid kanji phrase: contains no kanji')

        # Check prereqs if required
        prereq_cards: list[Card] = []
        if require_relationship:
            kana = []
            kanji = []
            if kana_phrase:
                kana += [k for k in kana_phrase if is_kana(k)]
            if kanji_phrase:
                kana += [k for k in kanji_phrase if is_kana(k)]
                kanji = [k for k in kanji_phrase if is_kanji(k)]
            kana = list(set(kana))
            kanji = list(set(kanji))

            for k in kana:
                kana_c = KanaCard.by_kana(k)
                if kana_c is None:
                    raise ValueError(f"Invalid kana or kanji phrase: contains unknown kana '{k}'")
                prereq_cards.append(kana_c.card)
            for k in kanji:
                kanji_c = KanjiCard.by_kanji(k)
                if kanji_c is None:
                    raise ValueError(f"Invalid kanji phrase: contains unknown kanji '{k}'")
                prereq_cards.append(kanji_c.card)
                    
            
        # Create new card object
        c = Card._create()

        # Generate a new relation object for every relationship
        if require_relationship:
            for prereq in prereq_cards:
                c.add_prereq(prereq)

        # Find new minimum id
        new_id = min(cls._id_cache, default=1) - 1

        #Instantiate and cache
        obj = PhraseCard(new_id, c, kanji_phrase, kana_phrase, meaning, grammar, False)
        cls._add_to_cache(obj)
        return obj


    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return

        with maybe_connection(con) as con2:
            for row in con2.execute(sqla.select(phrase_card_table)).mappings():
                if int(row['id']) in cls._id_cache:
                    continue
                _ = cls._create_from_mapping(row)
        cls._searched_db = True


    @classmethod
    def in_db(cls) -> list[PhraseCard]:
        cls._load_from_db()
        return [v for k, v in cls._id_cache.items() if k > 0]
    

    @classmethod
    def not_in_db(cls) -> list[PhraseCard]:
        return [v for k, v in cls._id_cache.items() if k < 1]


    @classmethod
    def every(cls) -> list[PhraseCard]:
        return cls.not_in_db() + cls.in_db()


    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> PhraseCard | None:
        obj = cls._id_cache.get(id)
        if obj is None:
            return obj
        elif  cls._searched_db:
            return

        with maybe_connection(con) as con2:
            stmnt = sqla.select(phrase_card_table)\
                        .where(phrase_card_table.c.id == id)
            res = con2.execute(stmnt)\
                      .mappings()\
                      .one_or_none()
            if res is not None:
                obj = PhraseCard._create_from_mapping(res)
        
        return obj


    # Constructor ##############################################################

    def __init__(self,
                 db_id: int,
                 card: Card,
                 kanji_phrase: str | None,
                 kana_phrase: str | None,
                 meaning: str,
                 grammar: str | None,
                 synced: bool):
        self._db_id = db_id
        self._card = card
        self._kanji_phrase = kanji_phrase
        self._kana_phrase = kana_phrase
        self._meaning = meaning
        self._grammar = grammar
        self._synced = synced

    @property
    def id(self) -> int:
        return self._db_id


    @property
    def card_id(self) -> int:
        return self._card._db_id

    @property
    def card(self) -> Card:
        return self._card

    @property
    def kanji_phrase(self) -> str | None:
        return self._kanji_phrase


    @kanji_phrase.setter
    def kanji_phrase(self, kp: str | None):
        if kp == '':
            kp = None

        if kp == self._kanji_phrase:
            return

        if kp:
            has_kanji = False
            for c in kp:
                if is_kanji(c):
                    has_kanji = True
                    break
            if not has_kanji:
                raise ValueError("Invalid kanji phrase: contains no kanji")

        self._kanji_phrase = kp
        self._synced = False
    
    @property
    def kana_phrase(self) -> str | None:
        return self._kana_phrase

    @kana_phrase.setter
    def kana_phrase(self, kp: str | None):
        if kp == '':
            kp = None

        if kp == self._kana_phrase:
            return
        
        if kp:
            for c in kp:
                if is_kanji(c):
                    raise ValueError(f"Invalid kana phrase: contains kanji '{c}'")

        self._kana_phrase = kp
        self._synced = False


    @property
    def meaning(self) -> str:
        return self._meaning

    @meaning.setter
    def meaning(self, m: str):
        if m is None or m == '':
            raise ValueError("Invalid meaning: cannot be None or empty string")
        if m != self._meaning:
            self._meaning = m
            self._synced = False


    @property
    def grammar(self) -> str | None:
        return self._grammar

    @grammar.setter
    def grammar(self, g: str | None):
        if g == '':
            g = None
        if g != self._grammar:
            self._grammar = g
            self._synced = False

    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def get_kanji(self) -> list[str]:
        ''' Returns all kanji found in the kanji phrase of this card'''
        if self._kanji_phrase:
            l = [k for k in self._kanji_phrase if is_kanji(k)]
            return list(set(l)) # remove duplicates
        return []

    def get_kana(self) -> list[str]:
        '''Returns all kana found in the kana and kanji phrase of this card'''
        l = []
        if self._kanji_phrase:
            l = [k for k in self._kanji_phrase if is_kana(k)]
        if self._kana_phrase:
            l += [k for k in self._kana_phrase if is_kana(k)]
        return list(set(l))


    def sync(self, con: sqla.Connection | None = None) -> int:

        with maybe_connection_commit(con) as con2:
            if not self.card.synced:
                c = self.card
                old_id = c.id
                self._card.sync(con=con2)
                if old_id != c.id:
                    self._synced = False

            # If already synced
            if self.synced:
                pass
            # If updating
            elif self._db_id > 0:
                res = con2.execute(
                    sqla.update(phrase_card_table)\
                        .where(phrase_card_table.c.id == self._db_id)\
                        .returning(phrase_card_table.c.id)\
                        .values(
                            kanji_phrase=self._kanji_phrase,
                            kana_phrase=self._kana_phrase,
                            meaning=self._meaning,
                            grammar=self._grammar))
                _ = res.scalar_one()
            # If creating
            else:
                PhraseCard._remove_from_cache(self)
                res = con2.execute(
                    sqla.insert(phrase_card_table)\
                        .returning(phrase_card_table.c.id)\
                        .values(
                            card_id=self._card._db_id,
                            kanji_phrase=self._kanji_phrase,
                            kana_phrase=self._kana_phrase,
                            meaning=self._meaning,
                            grammar=self._grammar))
                self._db_id = res.scalar_one()
                PhraseCard._add_to_cache(self)

        self._synced = True
        return self._db_id

