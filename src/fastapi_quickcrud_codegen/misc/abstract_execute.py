from typing import Any

from sqlalchemy.sql.elements import BinaryExpression


class SQLALchemyExecuteService(object):

    def __init__(self):
        pass

    @staticmethod
    def add(session, model) -> Any:
        session.add(model)

    @staticmethod
    def add_all(session, model) -> Any:
        session.add_all(model)

    @staticmethod
    async def async_flush(session) -> Any:
        await session.flush()

    @staticmethod
    def flush(session) -> Any:
        session.flush()

    @staticmethod
    async def async_execute(session, stmt: BinaryExpression) -> Any:
        return await session.execute(stmt)

    @staticmethod
    def execute(session, stmt: BinaryExpression) -> Any:
        return session.execute(stmt)

