# Author: Phillip Graham
# Description: Defines a class used to wrap the drawing table in the database
# Last Modified: Wed. Feb. 02, 2026

################################################################################
# Imports
################################################################################

from __future__ import annotations
from typing import Mapping
import sqlalchemy as sqla
from .database import _engine, drawing_table, maybe_connection

################################################################################
# Class Definition
################################################################################

class Drawing:
    # Class Variable ###########################################################

    _id_cache: dict[int, Drawing] = {}
    _stroke_count_groups: dict[int, dict[int, Drawing]] = {}
    _stroke_count_groups_searched_db: dict[int, bool] = {}
    _searched_db: bool = False

    # Class Methods ############################################################

    @classmethod
    def _add_to_cache(cls, d: Drawing):
        cls._id_cache[d._db_id] = d
        if d._stroke_count not in cls._stroke_count_groups:
            cls._stroke_count_groups[d._stroke_count] = {}
            cls._stroke_count_groups_searched_db[d._stroke_count] = False
        cls._stroke_count_groups[d._stroke_count][d._db_id] = d

    @classmethod
    def _clear_from_cache(cls, d: Drawing):
        del cls._id_cache[d._db_id]
        del cls._stroke_count_groups[d._stroke_count][d._db_id]
        if len(cls._stroke_count_groups[d._stroke_count]) == 0:
            del cls._stroke_count_groups[d._stroke_count]
            del cls._stroke_count_groups_searched_db[d._stroke_count]

    @classmethod
    def _create_from_mapping(cls, m: Mapping) -> Drawing:
        db_id = int(m['id'])
        if db_id in cls._id_cache:
            return cls._id_cache[db_id]
        stroke_count = int(m['stroke_count'])
        strokes = m['strokes']
        assert isinstance(strokes, list)
        
        obj = Drawing(db_id, stroke_count, strokes, True)
        cls._add_to_cache(obj)
        
        return obj

    @classmethod
    def create(cls, strokes: list[list[float]]) -> Drawing:
        new_id = min(cls._id_cache, default=1) - 1
        stroke_count = len(strokes)
        obj = Drawing(new_id, stroke_count, strokes, False)
        cls._add_to_cache(obj)
        return obj

    @classmethod
    def _load_from_db(cls, con: sqla.Connection | None = None):
        if cls._searched_db:
            return

        with maybe_connection(con) as con:
            for row in con.execute(sqla.select(drawing_table)).mappings():
                if int(row['id']) in cls._id_cache:
                    continue
                _ = cls._create_from_mapping(row)

        # Because we have searched every drawing we have also searched every stroke count
        for k in cls._stroke_count_groups_searched_db:
            cls._stroke_count_groups_searched_db[k] = True
        
        cls._searched_db = True

    @classmethod
    def in_db(cls) -> list[Drawing]:
        cls._load_from_db()
        return [v for k, v in cls._id_cache.items() if k > 0]
    
    @classmethod
    def not_in_db(cls) -> list[Drawing]:
        return [v for k, v in cls._id_cache.items() if k < 1]

    @classmethod
    def every(cls) -> list[Drawing]:
        return cls.not_in_db() + cls.in_db()
    
    @classmethod
    def by_id(cls, id: int, con: sqla.Connection | None = None) -> Drawing | None:
        obj = cls._id_cache.get(id)
        if obj:
            return obj
        elif cls._searched_db:
            return

        owns_con = False
        if con is None:
            owns_con = True
            con = _engine.connect()
        try:
            stmnt = sqla.select(drawing_table).where(drawing_table.c.id == id)
            res = con.execute(stmnt).mappings().one_or_none()
            if res is not None:
                obj = cls._create_from_mapping(res)
        finally:
            if owns_con:
                con.close()
        return obj
    
    @classmethod
    def by_stroke_count(cls, stroke_count: int, con: sqla.Connection | None = None) -> dict[int, Drawing] | None:
        if cls._stroke_count_groups_searched_db.get(stroke_count):
            return cls._stroke_count_groups[stroke_count]

        owns_con = False
        if con is None:
            owns_con = True
            con = _engine.connect()
        try:
            stmnt = sqla.select(drawing_table).where(drawing_table.c.stroke_count == stroke_count)
            res = con.execute(stmnt).mappings()
            for row in res:
                _ = cls._create_from_mapping(row)
        finally:
            if owns_con:
                con.close()
        return cls._stroke_count_groups.get(stroke_count)
        
    # Constructor ##############################################################

    def __init__(self, db_id: int, stroke_count: int, strokes: list[list[float]], synced: bool):
        self._db_id = db_id
        self._stroke_count = stroke_count
        self._strokes = strokes
        self._synced = synced

    # Properties ###############################################################

    @property
    def id(self) -> int:
        return self._db_id

    @property
    def stroke_count(self) -> int:
        return self._stroke_count

    @property
    def strokes(self) -> list[list[float]]:
        return self._strokes

    @strokes.setter
    def strokes(self, s: list[list[float]]):
        old_stroke_count = self._stroke_count
        self._stroke_count = len(s)
        self._strokes = s
        if old_stroke_count != self._stroke_count:
            Drawing._clear_from_cache(self)
            Drawing._add_to_cache(self)
        self._synced = False
        

    @property
    def synced(self) -> bool:
        return self._synced

    # Methods ##################################################################

    def sync(self, con: sqla.Connection | None = None) -> int:
        owns_con = False
        if con is None:
            owns_con = True
            con = _engine.connect()

        try:
            if self._db_id > 0:
                res = con.execute(
                    sqla.update(drawing_table)
                    .where(drawing_table.c.id == self._db_id)
                    .returning(drawing_table.c.id)
                    .values(stroke_count=self._stroke_count, strokes=self.strokes))
                _ = res.scalar_one()
            else:
                Drawing._clear_from_cache(self)
                res = con.execute(
                    sqla.insert(drawing_table)
                    .returning(drawing_table.c.id)
                    .values(
                        stroke_count=self._stroke_count,
                        strokes=self._strokes))
                self._db_id = res.scalar_one()
                Drawing._add_to_cache(self)
                
        finally:
            if owns_con:
                con.commit()
                con.close()
        self._synced = True
        return self._db_id
                
                
