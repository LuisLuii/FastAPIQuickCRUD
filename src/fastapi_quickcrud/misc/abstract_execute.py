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


class SQLALchemyExecuteService(object):

    def __init__(self):
        pass

    @staticmethod
    async def async_execute_and_expire(session, stmt):
        result = await session.execute(stmt)
        session.expire_all()
        return result

    @staticmethod
    def execute_and_expire(session, stmt):
        result = session.execute(stmt)
        session.expire_all()
        return result

    @staticmethod
    async def async_execute(session, stmt):
        return await session.execute(stmt)

    @staticmethod
    def execute(session, stmt):
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
