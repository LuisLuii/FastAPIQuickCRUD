from abc import ABC, abstractmethod


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

    async def async_execute_and_expire(self, session, stmt):
        result = await session.execute(stmt)
        session.expire_all()
        return result

    def execute_and_expire(self, session, stmt):
        result = session.execute(stmt)
        session.expire_all()
        return result

    async def async_execute(self, session, stmt):
        return await session.execute(stmt)

    def execute(self, session, stmt):
        return session.execute(stmt)


class DatabasesExecuteService():
    def __init__(self):
        raise NotImplementedError

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
