#
# class DBExecuteServiceBase(ABC):
#
#     @abstractmethod
#     async def async_execute(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def execute(self):
#         raise NotImplementedError
from typing import Any

from sqlalchemy.sql.elements import BinaryExpression


class SQLALchemyExecuteService(object):

    def __init__(self):
        pass

    @staticmethod
    async def async_execute_and_expire(session, stmt: BinaryExpression) -> Any:
        async_execute_and_expire_result = await session.execute(stmt)
        session.expire_all()
        return async_execute_and_expire_result

    @staticmethod
    def execute_and_expire(session, stmt: BinaryExpression) -> Any:
        execute_and_expire_result = session.execute(stmt)
        session.expire_all()
        return execute_and_expire_result

    @staticmethod
    async def async_execute(session, stmt: BinaryExpression) -> Any:
        return await session.execute(stmt)

    @staticmethod
    def execute(session, stmt: BinaryExpression) -> Any:
        return session.execute(stmt)




class DatabasesExecuteService:
    def __init__(self):
        pass

    # async def async_fetch_many(self, session, stmt):
    #     return await session.fetch_all(query=stmt)
    #
    # async def async_fetch_one(self, session, stmt,value):
    #     return await session.fetch_one(query=stmt, values=value)
    #
    # async def async_execute(self, session, stmt):
    #     return await session.execute(query=stmt)
    #
    # async def async_execute_many(self, session, stmt):
    #     return await session.execute_many(query=stmt)
