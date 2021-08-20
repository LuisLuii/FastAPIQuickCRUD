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
    async def async_execute(self):
        raise NotImplementedError

    @abstractmethod
    def execute(self):
        raise NotImplementedError

class SQLALchemyExecuteService(DBExecuteServiceBase):

    def __init__(self):
        pass

    async def async_execute_and_expire(self,session, stmt):
        result = await session.execute(stmt)
        session.expire_all()
        return result

    def execute_and_expire(self, session, stmt):
        result = session.execute(stmt)
        session.expire_all()
        return result

    async def async_execute(self,session, stmt):
        return await session.execute(stmt)

    def execute(self,session, stmt):
        return session.execute(stmt)


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