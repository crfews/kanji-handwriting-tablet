# Author: Phillip Graham
# Description: Defines a class used to wrap the kana card table in the database
# Last Modified: Sun. Feb. 08, 2026

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from .database import kana_card_table, maybe_connection, maybe_connection_commit
from .card import Card
from .drawing import Drawing
from .helpers import is_kana

################################################################################
# Class Definition
################################################################################

class KanaCard:
    # Class Variables ##########################################################

    _db_id_cache: dict[int, KanaCard] = {}
    _card_id_cache: dict[int, KanaCard] = {}
    _kana_cache: dict[str, KanaCard] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _add_to_cache(cls, kc: KanaCard):
        assert kc._db_id not in cls._db_id_cache
        assert kc.card.id not in cls._card_id_cache
        assert kc._kana not in cls._kana_cache
        cls._db_id_cache[kc._db_id] = kc
        cls._card_id_cache[kc.card.id] = kc
        cls._kana_cache[kc._kana] = kc

    @classmethod
    def _remove_from_cache(cls, kc: KanaCard):
        del cls._db_id_cache[kc._db_id]
        del cls._card_id_cache[kc.card.id]
        del cls._kana_cache[kc._kana]

    @classmethod
    def _create_from_mapping(cls, m: Mapping, con: sqla.Connection | None = None) -> KanaCard:
        db_id = int(m['id'])
        kana = str(m['kana'])

        # Guard from duplication
        if db_id in cls._db_id_cache:
            return cls._db_id_cache[db_id]
        
        # Get the card from the database
        card_id = int(m['card_id'])
        card = Card.by_id(card_id, con=con)
        if card is None:
            raise ValueError(f'Could not identify card of id: {card_id}')

        # Instantiate and cahce
        obj = KanaCard(
            db_id,
            card,
            m['drawing_id'],
            kana,
            m['romaji'],
            True)
        cls._add_to_cache(obj)
        
        return obj


    @classmethod
    def create(cls, kana: str, romaji: str):
        # Check parameters
        if not is_kana(kana):
            raise ValueError(f'Invalid kana: {kana} is not recognized as a kana character')
        if romaji is None or romaji == '':
            raise ValueError('Inavlid romaji: cannot be null or empty')
        
        # Check uniqueness
        extant_card = cls.by_kana(kana)
        if extant_card is not None:
            raise ValueError('Invalid kana: not unique')

        # Create new card object
        c = Card._create()

        # Find new minimum id
        new_id = min(cls._db_id_cache, default=1) - 1
        if new_id > 0:
            new_id = 0
        
        # Instantiate and cache
        obj = KanaCard(new_id, c, None, kana, romaji, False)
        cls._add_to_cache(obj)
        return obj


    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return

        with maybe_connection(con) as con2:
            for row in con2.execute(sqla.select(kana_card_table)).mappings():
                if int(row['id']) in cls._db_id_cache:
                    continue
                _ = cls._create_from_mapping(row)
        cls._searched_db = True


    @classmethod
    def in_db(cls) -> list[KanaCard]:
        cls._load_from_db()
        return [v for k, v in cls._db_id_cache.items() if k > 0]
    

    @classmethod
    def not_in_db(cls) -> list[KanaCard]:
        return [v for k, v in cls._db_id_cache.items() if k < 1]


    @classmethod
    def every(cls) -> list[KanaCard]:
        return cls.not_in_db() + cls.in_db()
    

    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> KanaCard | None:
        obj = cls._db_id_cache.get(id)
        if obj is None:
            return obj
        elif  cls._searched_db:
            return

        with maybe_connection(con) as con2:
            stmnt = sqla.select(kana_card_table)\
                        .where(kana_card_table.c.id == id)
            res = con2.execute(stmnt)\
                      .mappings()\
                      .one_or_none()
            if res is not None:
                obj = KanaCard._create_from_mapping(res)
        
        return obj

    @classmethod
    def by_card_id(cls, id:int, con: sqla.Connection | None = None) -> KanaCard | None:
        obj = cls._card_id_cache.get(id)
        if obj is not None:
            return obj
        elif  cls._searched_db:
            return

        with maybe_connection(con) as con:
            stmnt = sqla.select(kana_card_table)\
                        .where(kana_card_table.c.card_id == id)
            res = con.execute(stmnt)\
                     .mappings()\
                     .one_or_none()
            if res is not None:
                obj = KanaCard._create_from_mapping(res)
        return obj
    


    @classmethod
    def by_kana(cls, kana: str, con: sqla.Connection | None = None) -> KanaCard | None:
        obj = cls._kana_cache.get(kana)
        if obj is not None:
            return obj
        elif cls._searched_db:
            return

        with maybe_connection(con) as con2:
            stmnt = sqla.select(kana_card_table)\
                        .where(kana_card_table.c.kana == kana)
            res = con2.execute(stmnt)\
                      .mappings()\
                      .one_or_none()
            if res is not None:
                obj = KanaCard._create_from_mapping(res)
        
        return obj

    
    # Constructor ##############################################################

    def __init__(self,
                 idv: int,
                 card: Card,
                 drawing_id: int | None,
                 kana: str,
                 romaji: str,
                 synced: bool):
        self._db_id: int = idv
        self._card = card
        self._drawing_id = drawing_id
        self._kana = kana
        self._romaji = romaji
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
        if d.id == self._drawing_id:
            return
        elif not self._drawing_id is None:
            # Handle removing unused drawings
            pass
        self._drawing_id = d.id
        self._synced = False


    @property
    def kana(self) -> str:
        return self._kana


    @property
    def romaji(self) -> str:
        return self._romaji


    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def sync(self, con: sqla.Connection | None = None) -> int:

        with maybe_connection_commit(con) as con2:
            if not self.card.synced:
                c = self.card
                old_id = c.id
                self._card.sync(con=con2)
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
                    sqla.update(kana_card_table)\
                        .where(kana_card_table.c.id == self._db_id)\
                        .returning(kana_card_table.c.id)\
                        .values(drawing_id=self._drawing_id))
                _ = res.scalar_one()
            # If creating
            else:
                KanaCard._remove_from_cache(self)
                res = con2.execute(
                    sqla.insert(kana_card_table)\
                        .returning(kana_card_table.c.id)\
                        .values(
                            card_id=self._card._db_id,
                            drawing_id=self._drawing_id,
                            kana=self._kana,
                            romaji=self._romaji))
                self._db_id = res.scalar_one()
                KanaCard._add_to_cache(self)

        self._synced = True
        return self._db_id

