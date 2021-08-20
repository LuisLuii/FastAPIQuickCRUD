from abc import ABC, abstractmethod
from typing import List

from sqlalchemy import and_, text, select, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import BinaryExpression

from .exceptions import UnknownOrderType, UpdateColumnEmptyException, UnknownColumn
from .type import Ordering
from .utils import alias_to_column
from .utils import find_query_builder


class DBExecuteServiceBase(ABC):

    @abstractmethod
    def insert_one(self):
        raise NotImplementedError

    @abstractmethod
    def get_many(self):
        raise NotImplementedError

    @abstractmethod
    def get_one(self):
        raise NotImplementedError

    @abstractmethod
    def upsert(self):
        raise NotImplementedError

    @abstractmethod
    def delete(self):
        raise NotImplementedError

    @abstractmethod
    def update(self):
        raise NotImplementedError


class SQLALchemyExecuteService(DBExecuteServiceBase):

    def __init__(self):
        pass

    def insert_one(self):
        raise NotImplementedError

    def get_many(self):
        raise NotImplementedError

    def get_one(self, session, stmt):
        query_result = session.execute(stmt)
        return query_result

    async def async_get_one(self, session, stmt):
        query_result = await session.execute(stmt)
        return query_result

    def upsert(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError


class DatabasesExecuteService(DBExecuteServiceBase):

    def __init__(self):
        pass

    def insert_one(self):
        raise NotImplementedError

    def get_many(self):
        raise NotImplementedError
    def get_one(self):
        raise NotImplementedError

    async def async_get_one(self, session, stmt):
        query_result = await session.fetch_one(stmt)
        return query_result

    def upsert(self):
        raise NotImplementedError

    def delete(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError