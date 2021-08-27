from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

from fastapi_quickcrud import CrudMethods
from fastapi_quickcrud import crud_router_builder
from fastapi_quickcrud import sqlalchemy_table_to_pydantic
from fastapi_quickcrud import sqlalchemy_to_pydantic

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine('postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres', future=True, echo=True,
                             pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
async_session = sessionmaker(bind=engine, class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        async with session.begin():
            yield session


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, default=datetime.now(timezone.utc).strftime('%H:%M:%S%z'))


friend = Table(
    'friend', metadata,
    Column('id', ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend_name', String, nullable=False)
)

user_model_set = sqlalchemy_to_pydantic(db_model=User,
                                        crud_methods=[
                                            CrudMethods.FIND_MANY,
                                            CrudMethods.FIND_ONE,
                                            CrudMethods.UPSERT_ONE,
                                            CrudMethods.UPDATE_MANY,
                                            CrudMethods.UPDATE_ONE,
                                            CrudMethods.DELETE_ONE,
                                            CrudMethods.DELETE_MANY,
                                            CrudMethods.PATCH_MANY,

                                        ],
                                        exclude_columns=[])

friend_model_set = sqlalchemy_table_to_pydantic(db_model=friend,
                                                crud_methods=[
                                                    CrudMethods.FIND_MANY,
                                                    CrudMethods.UPSERT_MANY,
                                                    CrudMethods.UPDATE_MANY,
                                                    CrudMethods.DELETE_MANY,
                                                    CrudMethods.PATCH_MANY,

                                                ],
                                                exclude_columns=[])


crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=user_model_set,
                                   db_model=User,
                                   prefix="/user",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["User"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=friend_model_set,
                                   db_model=friend,
                                   async_mode=True,
                                   prefix="/friend",
                                   dependencies=[],
                                   tags=["Friend"]
                                   )


app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
