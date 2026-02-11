# Author: Phillip Graham
# Description: Defines a class used to wrap the kana card table in the database
# Last Modified: Mon. Feb. 09, 2026

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla

from data.kana_card import KanaCard
from .database import kanji_card_table, maybe_connection, maybe_connection_commit
from .card import Card
from .drawing import Drawing
from .helpers import is_kanji, is_kana

################################################################################
# Class Definition
################################################################################

class KanjiCard:
    # Class Variables ##########################################################

    _id_cache: dict[int, KanjiCard] = {}
    _card_id_cache: dict[int, KanjiCard] = {}
    _kanji_cache: dict[str, KanjiCard] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _add_to_cache(cls, kc: KanjiCard):
        assert kc._db_id not in cls._id_cache
        assert kc._kanji not in cls._kanji_cache
        cls._id_cache[kc._db_id] = kc
        cls._card_id_cache[kc.card.id] = kc
        cls._kanji_cache[kc._kanji] = kc


    @classmethod
    def _remove_from_cache(cls, kc: KanjiCard):
        del cls._id_cache[kc._db_id]
        del cls._kanji_cache[kc._kanji]
        del cls._card_id_cache[kc.card.id]


    @classmethod
    def _create_from_mapping(cls, m: Mapping, con: sqla.Connection | None = None) -> KanjiCard:
        db_id = int(m['id'])
        kanji = str(m['kanji'])

        # Guard from duplication
        if db_id in cls._id_cache:
            return cls._id_cache[db_id]

        # Get the card from the database
        card_id = int(m['card_id'])
        card = Card.by_id(card_id, con=con)
        if card is None:
            raise ValueError(f'Could not identify card of id: {card_id}')

        # Instantiate and cahce
        obj = KanjiCard(
            db_id,
            card,
            m['drawing_id'],
            kanji,
            m['on_yomi'],
            m['kun_yomi'],
            m['meaning'],
            True)
        cls._add_to_cache(obj)
        
        return obj

    @classmethod
    def create(cls,
               kanji: str,
               on_yomi: str | None = None,
               kun_yomi: str | None = None,
               meaning: str | None = None,
               require_relationships: bool = True):
        # Check parameters
        if not is_kanji(kanji):
            raise ValueError(f'Invalid kanji: {kanji} not recognized as a kanji character')
        if on_yomi:
            on_yomi = on_yomi.strip()
        if kun_yomi:
            kun_yomi = kun_yomi.strip()
        if on_yomi == '':
            on_yomi = None
        if kun_yomi == '':
            kun_yomi = None
        if on_yomi is None and kun_yomi is None:
            raise ValueError('Invalid on_yomi or kun_yomi: both cannot be None or empty')
        if on_yomi is not None:
            has_kana = False
            for c in on_yomi:
                if is_kana(c):
                    has_kana = True
                    break
            if not has_kana:
                raise ValueError('Invalid on_yomi: contains no kana')
        if kun_yomi is not None:
            has_kana = False
            for c in kun_yomi:
                if is_kana(c):
                    has_kana = True
                    break
            if  not has_kana:
                raise ValueError('Invalid kun_yomi: contains no kana')
                
        # Check uniqueness
        extant_card = cls.by_kanji(kanji)
        if extant_card is not None:
            raise ValueError('Invalid kanji: not unique')
        
        # Check prereqs if required
        kana_cards = []
        if require_relationships:
            kana = []
            if on_yomi:
                kana = [k for k in on_yomi if is_kana(k)]
            if kun_yomi:
                kana += [k for k in kun_yomi if is_kana(k)]
            kana = list(set(kana))

            for k in kana:
                kana_c = KanaCard.by_kana(k)
                if not kana_c:
                    raise ValueError(f"Invalid on_yomi or kun_yomi: uknown kana '{k}'")
                kana_cards.append(kana_c)
        
        # Create new card object
        c = Card._create()

        # If set to do so generate a new relation object for every kana relationship
        if require_relationships:
            for kana_c in kana_cards:
                c.add_prereq(kana_c.card)
        
        # Find new minimum id
        new_id = min(cls._id_cache, default=1) - 1
        if new_id > 0:
            new_id = 0

        # Instantiate and cache
        obj = KanjiCard(new_id, c, None, kanji, on_yomi, kun_yomi, meaning, False)
        cls._add_to_cache(obj)
        
        return obj


    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return
        with maybe_connection(con) as con2:
            for row in con2.execute(sqla.select(kanji_card_table)).mappings():
                if int(row['id']) in cls._id_cache:
                    continue
                _ = cls._create_from_mapping(row)
        cls._searched_db = True


    @classmethod
    def in_db(cls) -> list[KanjiCard]:
        cls._load_from_db()
        return [v for k, v in cls._id_cache.items() if k > 0]
    

    @classmethod
    def not_in_db(cls) -> list[KanjiCard]:
        return [v for k, v in cls._id_cache.items() if k < 1]


    @classmethod
    def every(cls) -> list[KanjiCard]:
        return cls.not_in_db() + cls.in_db()
    

    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> KanjiCard | None:
        # check cache
        obj = cls._id_cache.get(id)
        if obj is not None:
            return obj
        elif  cls._searched_db:
            return

        with maybe_connection(con) as con2:
            stmnt = sqla.select(kanji_card_table)\
                        .where(kanji_card_table.c.id == id)
            res = con2.execute(stmnt)\
                      .mappings()\
                      .one_or_none()
            if res is not None:
                obj = KanjiCard._create_from_mapping(res)
        return obj


    @classmethod
    def by_card_id(cls, id:int, con: sqla.Connection | None = None) -> KanjiCard | None:
        obj = cls._card_id_cache.get(id)
        if obj is not None:
            return obj
        elif  cls._searched_db:
            return

        with maybe_connection(con) as con:
            stmnt = sqla.select(kanji_card_table)\
                        .where(kanji_card_table.c.card_id == id)
            res = con.execute(stmnt)\
                     .mappings()\
                     .one_or_none()
            if res is not None:
                obj = KanjiCard._create_from_mapping(res)
        return obj
    
    @classmethod
    def by_kanji(cls, kanji: str, con: sqla.Connection | None = None) -> KanjiCard | None:
        # Check cache
        obj = cls._kanji_cache.get(kanji)
        if obj is not None:
            return obj
        elif cls._searched_db:
            return

        with maybe_connection(con) as con2:
            stmnt = sqla.select(kanji_card_table)\
                        .where(kanji_card_table.c.kanji == kanji)
            res = con2.execute(stmnt)\
                      .mappings()\
                      .one_or_none()
            if res is not None:
                obj = KanjiCard._create_from_mapping(res)
        return obj

    
    # Constructor ##############################################################

    def __init__(self,
                 db_id: int,
                 card: Card,
                 drawing_id: int | None,
                 kanji: str,
                 on_yomi: str | None,
                 kun_yomi: str | None,
                 meaning: str | None,
                 synced: bool):
        self._db_id: int = db_id
        self._card = card
        self._drawing_id = drawing_id
        self._kanji = kanji
        self._on_yomi = on_yomi
        self._kun_yomi = kun_yomi
        self._meaning = meaning
        self._synced = synced
               
    # Properties ###############################################################

    @property
    def id(self) -> int:
        return self._db_id


    @property
    def card(self) -> Card:
        return self._card


    @property
    def drawing(self) -> Drawing | None:
        if self._drawing_id is not None:
            return Drawing.by_id(self._drawing_id)
        

    @drawing.setter
    def drawing(self, d: Drawing):
        if d._db_id == self._drawing_id:
            return
        elif self._drawing_id != -1:
            # Handle removing unused drawings
            pass
        self._drawing_id = d.id
        self._synced = False


    @property
    def kanji(self) -> str:
        return self._kanji


    @property
    def on_yomi(self) -> str | None:
        return self._on_yomi
    

    @on_yomi.setter
    def on_yomi(self, oy: str | None):
        if oy == self._on_yomi:
            return
        self._on_yomi = oy
        self._synced = False


    @property
    def kun_yomi(self) -> str | None:
        return self._kun_yomi


    @kun_yomi.setter
    def kun_yomi(self, ky: str | None):
        if ky == self._on_yomi:
            return
        self._kun_yomi = ky
        self._synced = False


    @property
    def meaning(self) -> str | None:
        return self._meaning


    @meaning.setter
    def meaning(self, m: str | None):
        if m == self._meaning:
            return
        self._meaning = m
        self._synced
    

    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def sync(self, con: sqla.Connection | None = None) -> int:
        with maybe_connection_commit(con) as con2:
            if not self._card.synced:
                c = self.card
                old_id = c.id
                self.card.sync(con=con2)
                if old_id != c.id:
                    self._synced = False
            if self.drawing and not self.drawing.synced:
                dw = self.drawing
                old_id = dw.id
                dw.sync(con=con2)
                if old_id != dw.id:
                    self._drawing_id = dw.id
                    self._synced = False

            # If already synced
            if self.synced:
                pass
            # If updating
            elif self._db_id > 0:
                res = con2.execute(
                    sqla.update(kanji_card_table)\
                        .where(kanji_card_table.c.id == self._db_id)\
                        .returning(kanji_card_table.c.id)\
                        .values(
                            drawing_id=self._drawing_id,
                            kun_yomi=self._kun_yomi,
                            on_yomi=self._on_yomi,
                            meaning=self._meaning))
                _ = res.scalar_one()
            # If creating
            else:
                KanjiCard._remove_from_cache(self)
                res = con2.execute(
                    sqla.insert(kanji_card_table)\
                        .returning(kanji_card_table.c.id)\
                        .values(
                            card_id=self._card._db_id,
                            drawing_id=self._drawing_id,
                            kanji=self._kanji,
                            on_yomi=self._on_yomi,
                            kun_yomi=self._kun_yomi,
                            meaning=self._meaning))
                self._db_id = res.scalar_one()
                KanjiCard._add_to_cache(self)

        self._synced = True
        return self._db_id

