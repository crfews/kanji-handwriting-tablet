# Author: Phillip Graham
# Description: Defines a class used to wrap the table of relationships between
# cards
# Last Modified: Wed. Feb. 02, 2026
 

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from .database import _engine, card_relation_table, maybe_connection, maybe_connection_commit
#from .card import Card
from typing import TYPE_CHECKING

# satisfy pyright
if TYPE_CHECKING:
    from .card import Card
    
################################################################################
# Class Definition
################################################################################

class CardRelation:
    # Class Variables ##########################################################
    _instances_by_id: dict[int, CardRelation] = {}
    _instances_by_a_id: dict[int, dict[int, CardRelation]] = {}
    _instances_by_a_id_searched_db: dict[int, bool] = {}
    _instances_by_b_id: dict[int, dict[int, CardRelation]] = {}
    _instances_by_b_id_searched_db: dict[int,bool] = {}
    _searched_db: bool = False

    # Class Methods ############################################################
    @classmethod
    def _add_to_cache(cls, cr: CardRelation):
        assert cr._db_id not in cls._instances_by_id
        a_group = cls._instances_by_a_id.get(cr._card_a_id)
        if a_group:
            assert cr._db_id not in a_group
        b_group = cls._instances_by_b_id.get(cr._card_b_id)
        if b_group:
            assert cr._db_id not in b_group

        cls._instances_by_id[cr._db_id] = cr
        if not a_group:
            cls._instances_by_a_id[cr._card_a_id] = {}
        cls._instances_by_a_id[cr._card_a_id][cr._db_id] = cr
        if not b_group:
            cls._instances_by_b_id[cr._card_b_id] = {}
        cls._instances_by_b_id[cr._card_b_id][cr._db_id] = cr

    @classmethod
    def _clear_from_cache(cls, cr: CardRelation):
        del cls._instances_by_id[cr._db_id]
        del cls._instances_by_a_id[cr._card_a_id][cr._db_id]
        del cls._instances_by_b_id[cr._card_b_id][cr._db_id]
        

    @classmethod
    def _create_from_mapping(cls, m: Mapping):
        db_id = int(m['id'])

        # Avoid duplicates
        obj = cls._instances_by_id.get(db_id)
        if not obj:
            obj = CardRelation(db_id,
                                   int(m['card_a_id']),
                                   int(m['card_b_id']),
                                   bool(m['b_is_prereq']),
                                   bool(m['easily_confused']),
                                   True)
            cls._add_to_cache(obj)
        return obj
    
    @classmethod
    def _create(cls,
                card_a: "Card",
                card_b: "Card",
                b_is_prereq: bool,
                easily_confused: bool) -> CardRelation:
        if card_a.id == card_b.id or card_a == card_b:
            raise ValueError('Invalid ids: a card cannot be related to itself')
    
        new_id = min(cls._instances_by_id, default=1) -1          
        obj = cls(new_id, card_a.id, card_b.id, b_is_prereq, easily_confused, False)
        cls._add_to_cache(obj)
        return obj

    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return

        owns_con = False
        if con is None:
            owns_con = True
            con = _engine.connect()
        try:
            for row in con.execute(sqla.select(card_relation_table)).mappings():
                if int(row['id']) in cls._instances_by_id:
                    continue
                _ = cls._create_from_mapping(row)
        finally:
            if owns_con:
                con.close()

        for k in cls._instances_by_a_id_searched_db:
            cls._instances_by_a_id_searched_db[k] = True
        for k in cls._instances_by_b_id_searched_db:
            cls._instances_by_b_id_searched_db[k] = True
        cls._searched_db = True
        
    @classmethod
    def in_db(cls) -> list[CardRelation]:
        cls._load_from_db()
        return [v for k, v in cls._instances_by_id.items() if k > 0]

    @classmethod
    def not_in_db(cls) -> list[CardRelation]:
        return [v for k, v in cls._instances_by_id.items() if k < 1]

    @classmethod
    def every(cls) -> list[CardRelation]:
        return cls.not_in_db() + cls.in_db()
                                   
    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> CardRelation | None:
        # If the object is already cached immediately return
        # If the object was not cached and we have already searched return None
        obj = cls._instances_by_id.get(id)
        if obj:
            return obj
        elif cls._searched_db:
            return

        # Otherwise find this specific element and cache it
        with maybe_connection(con) as con:
            stmnt = sqla.select(card_relation_table).where(card_relation_table.c.id == id)
            res = con.execute(stmnt).mappings().one_or_none()
            if res is not None:
                obj = cls._create_from_mapping(res)
            
        return obj

    @classmethod
    def by_a_id(cls, a_id: int, con: sqla.Connection | None = None) -> dict[int, CardRelation] | None:
        if cls._instances_by_a_id_searched_db.get(a_id) is True:
            return cls._instances_by_a_id[a_id]

        with maybe_connection(con) as con:
            stmnt = sqla.select(card_relation_table).where(card_relation_table.c.card_a_id == a_id)
            res = con.execute(stmnt).mappings()
            for row in res:
                _ = cls._create_from_mapping(row)
        return cls._instances_by_a_id.get(a_id)

    @classmethod
    def by_b_id(cls, b_id: int, con: sqla.Connection | None = None) -> dict[int, CardRelation] | None:
        if cls._instances_by_b_id_searched_db.get(b_id) is True:
            return cls._instances_by_b_id[b_id]

        with maybe_connection(con) as con:
            stmnt = sqla.select(card_relation_table).where(card_relation_table.c.card_b_id == b_id)
            res = con.execute(stmnt).mappings()
            for row in res:
                _ = cls._create_from_mapping(row)
        return cls._instances_by_b_id.get(b_id)
    

    @classmethod
    def specifc_relation(cls,
                         a_id: int,
                         b_id: int,
                         b_is_prereq: bool | None = None,
                         easily_confused: bool | None = None,
                         con: sqla.Connection | None = None) -> CardRelation | None:
        a_relations = cls.by_a_id(a_id,con=con)
        if a_relations is None:
            return
        for _, v in a_relations.items():
            if b_is_prereq is not None and easily_confused is not None:
                if v.card_b_id == b_id\
                   and v.b_is_prereq == b_is_prereq\
                   and v.easily_confused == easily_confused:
                    return v
            elif b_is_prereq is not None:
                if v.card_b_id == b_id and v.b_is_prereq == b_is_prereq:
                    return v
            elif easily_confused is not None:
                if v.card_b_id == b_id and v.easily_confused == easily_confused:
                    return v
            else:
                if v.card_b_id == b_id:
                    return v
                    
            
                        
    # Constructor ##############################################################

    def __init__(self,
                 db_id: int,
                 card_a_id: int,
                 card_b_id: int,
                 b_is_prereq: bool,
                 easily_confused: bool,
                 synced: bool):
        self._db_id = db_id
        self._card_a_id = card_a_id
        self._card_b_id = card_b_id
        self._b_is_prereq = b_is_prereq
        self._easily_confused = easily_confused
        self._synced = synced

    # Properties ###############################################################

    @property
    def id(self) -> int:
        return self._db_id

    @property
    def card_a_id(self) -> int:
        return self._card_a_id

    @property
    def card_b_id(self) -> int:
        return self._card_b_id

    @property
    def b_is_prereq(self) -> bool:
        return self._b_is_prereq

    @b_is_prereq.setter
    def b_is_prereq(self, b: bool):
        if b == self._b_is_prereq:
            return
        self._b_is_prereq = b
        self._synced = False

    @property
    def easily_confused(self) -> bool:
        return self._easily_confused

    @easily_confused.setter
    def easly_confused(self, b: bool):
        if b == self._easily_confused:
            return
        self._easily_confused = b
        self._synced = False
        
    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def sync(self, con: sqla.Connection | None = None) -> int:
        # Ignore reduntant syncs
        if self.synced:
            return self._db_id
        
        owns_con = False
        if con is None:
            owns_con = True
            con = _engine.connect()

        try:
            if self._db_id > 0:
                res = con.execute(
                    sqla.update(card_relation_table)
                    .where(card_relation_table.c.id == self._db_id)
                    .returning(card_relation_table.c.id)
                    .values(card_a_id=self._card_a_id,
                            card_b_id=self._card_b_id,
                            b_is_prereq=self._b_is_prereq,
                            easily_confused=self._easily_confused))
                _ = res.scalar_one()
            else:
                CardRelation._clear_from_cache(self)
                res = con.execute(
                    sqla.insert(card_relation_table)
                    .returning(card_relation_table.c.id)
                    .values(
                        b_is_prereq=self._b_is_prereq,
                        tags=self._b_is_prereq))
                self._db_id = res.scalar_one()
                CardRelation._add_to_cache(self)
        finally:
            if owns_con:
                con.commit()
                con.close()

        self._synced = True
        return self._db_id
