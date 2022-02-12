import asyncio
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey, DateTime, Text, text, select, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from fastapi_quickcrud import CrudMethods
from fastapi_quickcrud import crud_router_builder
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
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, LargeBinary, Numeric, SmallInteger, String, Table, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Parent(Base):
    __tablename__ = 'parent_one_to_many_back_ref'
    id = Column(Integer, primary_key=True)
    children = relationship("Child", backref="parent_one_to_many_back_ref")

class Child(Base):
    __tablename__ = 'child_one_to_many_back_ref'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent_one_to_many_back_ref.id'))


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)



user_model_set = sqlalchemy_to_pydantic(db_model=Parent,
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

friend_model_set = sqlalchemy_to_pydantic(db_model=Child,
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
                                   db_model=Parent,
                                   prefix="/Parent",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["Parent"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=friend_model_set,
                                   db_model=Child,
                                   async_mode=True,
                                   prefix="/Child",
                                   dependencies=[],
                                   tags=["Child"]
                                   )


app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
