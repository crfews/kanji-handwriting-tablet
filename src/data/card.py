# Author: Phillip Graham
# Description: Defines a class used to wrap the card table in the database
# Last Modified: Wed. Feb. 02, 2026
 

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from datetime import date
from .database import card_table, maybe_connection, maybe_connection_commit
from .card_relation import CardRelation

################################################################################
# Class Definition
################################################################################

class Card:
    # Class Variables ##########################################################

    _id_cache: dict[int, Card] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _add_to_cache(cls, kc: Card):
        assert kc._db_id not in cls._id_cache
        cls._id_cache[kc._db_id] = kc


    @classmethod
    def _remove_from_cache(cls, kc: Card):
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
        cls._add_to_cache(obj)
        
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

        # Instantiate and cache
        obj = cls(new_id, study_id, due_date_increment, due_date, tags, False)
        cls._add_to_cache(obj)
        
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
            if self._db_id == cr._card_a_id:
                c = Card.by_id(cr._card_b_id)
            elif self._db_id == cr._card_b_id:
                c = Card.by_id(cr._card_a_id)
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


    def sync(self, con: sqla.Connection | None = None) -> int:
        with maybe_connection_commit(con) as con2:
            for r in self.relations:
                if not r.synced:
                    r.sync(con=con2)
                    
            # Ignore reduntant syncs
            if self.synced:
                pass
            # If updating
            elif self._db_id > 0:
                res = con2.execute(
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
                old_id = self._db_id
                res = con2.execute(
                    sqla.insert(card_table)\
                        .returning(card_table.c.id)\
                        .values(
                            study_id=self._study_id,
                            due_date_increment=self._due_date_increment,
                            due_date=self._due_date,
                            tags=self._tags))
                self._db_id = res.scalar_one()
                del Card._id_cache[old_id]
                Card._id_cache[self._db_id] = self

        self._synced = True
        return self._db_id
