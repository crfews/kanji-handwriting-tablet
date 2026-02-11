# Author: Phillip Graham
# Description: Defines a class used to wrap the card table in the database
# Last Modified: Tue. Feb. 10, 2026
 

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from datetime import date
from .database import card_table, card_relation_table, maybe_connection, maybe_connection_commit

################################################################################
# Class Definition
################################################################################


class CardRelation:
    # Class Variables ##########################################################
    _instances_by_id: dict[int, CardRelation] = {}
    _searched_db_a_id: dict[int, bool] = {}
    _searched_db_b_id: dict[int, bool] = {}
    _searched_db: bool = False
    
    # Class Methods ############################################################
    @classmethod
    def _encache(cls, cr: CardRelation):
        assert cr._db_id not in cls._instances_by_id
        cls._instances_by_id[cr._db_id] = cr

    @classmethod
    def _decache(cls, cr: CardRelation):
        del cls._instances_by_id[cr._db_id]

    @classmethod
    def _create_from_mapping(cls, m: Mapping):
        db_id = int(m['id'])

        # Avoid duplicates
        obj = cls._instances_by_id.get(db_id)
        if not obj:
            card_a = Card.by_id(m['card_a_id'])
            assert card_a
            card_b = Card.by_id(m['card_b_id'])
            assert card_b
            obj = CardRelation(db_id,
                                   card_a,
                                   card_b,
                                   bool(m['b_is_prereq']),
                                   bool(m['easily_confused']),
                                   True)
            cls._encache(obj)
        return obj
    
    @classmethod
    def _create(cls,
                card_a: Card,
                card_b: Card,
                b_is_prereq: bool,
                easily_confused: bool) -> CardRelation:
        if card_a.id == card_b.id or card_a == card_b:
            raise ValueError('Invalid ids: a card cannot be related to itself')
    
        new_id = min(cls._instances_by_id, default=1) -1
        if new_id > 0:
            new_id = 0
        
            
        obj = cls(new_id, card_a, card_b, b_is_prereq, easily_confused, False)
        cls._encache(obj)
        return obj


    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return

        with maybe_connection(con) as con:
            for row in con.execute(sqla.select(card_relation_table)).mappings():
                if int(row['id']) in cls._instances_by_id:
                    continue
                _ = cls._create_from_mapping(row)
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
        d = {}
        
        if a_id > 0:
            with maybe_connection(con) as con:
                stmnt = sqla.select(card_relation_table).where(card_relation_table.c.card_a_id == a_id)
                res = con.execute(stmnt).mappings()
                for row in res:
                    obj = cls._create_from_mapping(row)
                    d[obj.id] = obj
            cls._searched_db_a_id[a_id] = True

        for r in [r for k, r in cls._instances_by_id.items() if k < 1]:
            if r._card_a.id == a_id:
                d[r.id] = r
        
        return d



    @classmethod
    def by_b_id(cls, b_id: int, con: sqla.Connection | None = None) -> dict[int, CardRelation] | None:
        d = {}

        if b_id > 0:
            with maybe_connection(con) as con:
                stmnt = sqla.select(card_relation_table).where(card_relation_table.c.card_b_id == b_id)
                res = con.execute(stmnt).mappings()
                for row in res:
                    obj = cls._create_from_mapping(row)
                    d[obj.id] = obj
            cls._searched_db_b_id[b_id] = True

        for r in [r for k, r in cls._instances_by_id.items() if k < 1]:
            if r._card_b.id == b_id:
                d[r.id] = r
                
        return d
    

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
                 card_a: Card,
                 card_b: Card,
                 b_is_prereq: bool,
                 easily_confused: bool,
                 synced: bool):
        self._db_id = db_id
        self._card_a = card_a
        self._card_b = card_b
        self._b_is_prereq = b_is_prereq
        self._easily_confused = easily_confused
        self._synced = synced

    # Properties ###############################################################

    @property
    def id(self) -> int:
        return self._db_id

    @property
    def card_a_id(self) -> int:
        return self._card_a.id

    @property
    def card_a(self) -> Card:
        return self._card_a
    
    @property
    def card_b_id(self) -> int:
        return self._card_b.id

    @property
    def card_b(self) -> Card:
        return self._card_b
    
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

        with maybe_connection_commit(con) as con:
            
            if self._db_id > 0:
                # These should never fail
                assert self._card_a.id > 0
                assert self._card_b.id > 0
                
                res = con.execute(
                    sqla.update(card_relation_table)
                    .where(card_relation_table.c.id == self._db_id)
                    .returning(card_relation_table.c.id)
                    .values(b_is_prereq=self._b_is_prereq,
                            easily_confused=self._easily_confused))
                _ = res.scalar_one()
            else:
                CardRelation._decache(self)
                if self._card_a.id < 1:
                    self._card_a._sync_only_self(con)
                if self._card_b.id < 1:
                    self._card_b._sync_only_self(con)
                    
                res = con.execute(
                    sqla.insert(card_relation_table)
                    .returning(card_relation_table.c.id)
                    .values(card_a_id=self._card_a.id,
                            card_b_id=self._card_b.id,
                            b_is_prereq=self._b_is_prereq,
                            easily_confused=self._easily_confused))
                self._db_id = res.scalar_one()
                CardRelation._encache(self)

        self._synced = True
        return self._db_id


















class Card:
    # Class Variables ##########################################################

    _id_cache: dict[int, Card] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _encache(cls, kc: Card):
        assert kc._db_id not in cls._id_cache
        cls._id_cache[kc._db_id] = kc


    @classmethod
    def _decache(cls, kc: Card):
        del cls._id_cache[kc._db_id]


    @classmethod
    def _create_from_mapping(cls, m: Mapping):
        db_id = int(m['id'])

        # Guard from duplication
        if db_id in cls._id_cache:
            return cls._id_cache[db_id]

        # Satisfy type checker
        due_date = m['due_date']
        if not isinstance(due_date, date):
            raise ValueError(f'Invalid type: {type(due_date)}')

        # Instantiate and cache
        obj = Card(db_id,
                   int(m['study_id']),
                   int(m['due_date_increment']),
                   due_date,
                   str(m['tags']),
                   True)
        cls._encache(obj)
        
        return obj
    

    @classmethod
    def _create(cls,
               study_id: int | None = None,
               due_date_increment: int | None = None,
               due_date: date | None = None,
               tags: str | None = None) -> Card:
        # Check parameters
        if study_id is None:
            study_id = -1
        if due_date_increment is None:
            due_date_increment = 0
        if due_date is None:
            due_date = date.today()

        # Find new minimum id
        new_id = min(cls._id_cache, default=1) - 1
        if new_id > 0:
            new_id = 0
        
        # Instantiate and cache
        obj = cls(new_id, study_id, due_date_increment, due_date, tags, False)
        cls._encache(obj)
        
        return obj


    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return
        with maybe_connection(con) as con2:
            for row in con2.execute(sqla.select(card_table)).mappings():
                if int(row['id']) in cls._id_cache:
                    continue
                _ = cls._create_from_mapping(row)
        cls._searched_db = True
        

    @classmethod
    def in_db(cls) -> list[Card]:
        cls._load_from_db()
        return [v for k, v in cls._id_cache.items() if k > 0]


    @classmethod
    def not_in_db(cls) -> list[Card]:
        return [v for k, v in cls._id_cache.items() if k < 1]


    @classmethod
    def every(cls) -> list[Card]:
        return cls.not_in_db() + cls.in_db()
                                   
    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> Card | None:
        # check cache
        obj = cls._id_cache.get(id)
        if obj:
            return obj
        elif cls._searched_db:
            return

        # Otherwise find this specific element and cache it
        with maybe_connection(con) as con2:
            stmnt = sqla.select(card_table).where(card_table.c.id == id)
            res = con2.execute(stmnt).mappings().one_or_none()
            if res is not None:
                obj = cls._create_from_mapping(res)
            
        return obj
    
    # Constructor ##############################################################

    def __init__(self,
                 db_id: int,
                 study_id: int,
                 due_date_increment: int,
                 due_date: date,
                 tags: str | None,
                 synced: bool):
        self._db_id = db_id
        self._study_id = study_id
        self._due_date_increment = due_date_increment
        self._due_date = due_date
        self._tags = tags
        self._synced = synced

    # Properties ###############################################################

    @property
    def id(self) -> int:
        return self._db_id


    @property
    def study_id(self) -> int:
        return self._study_id


    @study_id.setter
    def study_id(self, id: int):
        if id == self._study_id:
            return
        self._study_id = id
        self._synced = False
    

    @property
    def due_date_increment(self) -> int:
        return self._due_date_increment


    @due_date_increment.setter
    def due_date_increment(self, incr: int):
        if incr == self._due_date_increment:
            return
        self._due_date_increment = incr
        self._synced = False


    @property
    def due_date(self) -> date:
        return self._due_date


    @due_date.setter
    def due_date(self, d: date):
        if d == self._due_date:
            return
        self._due_date = d
        self._synced = False
        

    @property
    def tags(self) -> str:
        if self._tags is None:
            return ''
        return self._tags


    @property
    def tags_list(self) -> list[str]:
        if self._tags is None:
            return []
        return self._tags.split(',')


    @property
    def relations(self) -> list[CardRelation]:
        a_group = CardRelation.by_a_id(self._db_id)
        b_group = CardRelation.by_b_id(self._db_id)

        if a_group:
            a_group = [v for _, v in a_group.items()]
        else:
            a_group = []
        if b_group:
            b_group = [v for _, v in b_group.items()]
        else:
            b_group = []
        return a_group + b_group
    

    @property
    def prerequisites(self) -> list[Card]:
        rel = self.relations
        def assert_card(c: Card | None) -> Card:
            assert c
            return c
        return [assert_card(Card.by_id(r.card_b_id))
                for r
                in rel
                if r.b_is_prereq and r.card_a_id == self._db_id]

    @property
    def easily_confused(self) -> list[Card]:
        rel = self.relations
        def a_if_b_b_if_a(cr: CardRelation) -> Card:
            c = None
            if self._db_id == cr.card_a_id:
                c = Card.by_id(cr.card_b_id)
            elif self._db_id == cr.card_b_id:
                c = Card.by_id(cr.card_a_id)
            assert c
            return c
        return [a_if_b_b_if_a(r)
                for r
                in rel
                if r.easily_confused]
            
            
    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def add_prereq(self, c: Card) -> CardRelation:
        assert isinstance(c, Card)
        # Check to see that this relationship already exists
        r = CardRelation.specifc_relation(self.id, c.id)
        if r is not None and r.b_is_prereq:
            return r
        elif r is not None:
            r.b_is_prereq = True
            return r
        else:
            return CardRelation._create(self, c, True, False)
    

    def add_easily_confused(self, c: Card):
        # Check to see that this relationship already exists
        r = CardRelation.specifc_relation(self.id, c.id)
        if r is not None and r.b_is_prereq:
            return r
        elif r is not None:
            r.b_is_prereq = True
            return r
        else:
            return CardRelation._create(self, c, True, False)
    

    def clear_tags(self):
        if self._tags is None or self._tags == '':
            return
        self._tags = None
        self._synced = False


    def add_tag(self, t: str):
        if ',' in t:
            raise ValueError('Tags may not contain commas')
        if self._tags is None:
            self._tags = t
        else:
            self._tags = self._tags + f',{t}'


    def remove_tag(self, t: str):
        if self._tags is None or self._tags == '':
            return
        new_tags = self._tags.split(',')
        if t in new_tags:
            new_tags.remove(t)
            self._tags = ','.join(new_tags)
            self._synced = False


    def _sync_only_self(self, con: sqla.Connection | None = None) -> int:
        with maybe_connection_commit(con) as con:
            # Ignore reduntant syncs
            if self.synced:
                pass
            # If updating
            elif self._db_id > 0:
                res = con.execute(
                    sqla.update(card_table)\
                        .where(card_table.c.id == self._db_id)\
                        .returning(card_table.c.id)\
                        .values(due_date=self._due_date,
                                due_date_increment=self._due_date_increment,
                                tags=self._tags,
                                study_id=self._study_id))
                _ = res.scalar_one()
            # If inserting
            else:
                Card._decache(self)
                res = con.execute(
                    sqla.insert(card_table)\
                        .returning(card_table.c.id)\
                        .values(study_id=self._study_id,
                                due_date_increment=self._due_date_increment,
                                due_date=self._due_date,
                                tags=self._tags))
                self._db_id = res.scalar_one()
                Card._encache(self)
        self._synced = True
        return self._db_id
        

    def sync(self, con: sqla.Connection | None = None) -> int:
        with maybe_connection_commit(con) as con:
            for r in self.relations:
                if not r.synced:
                    r.sync(con=con)
            self._sync_only_self(con)
        return self._db_id
