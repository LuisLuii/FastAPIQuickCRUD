from enum import auto

import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from strenum import StrEnum

from fastapi_quickcrud import crud_router_builder

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


# friend = Table(
#     'test_friend', metadata,
#     Column('id', ForeignKey('test_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
#     Column('friend_name', String, nullable=False)
# )

#
# class friend(Base):
#     __tablename__ = 'test_friend'
#
#     id = Column(ForeignKey('test_users.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
#     friend_name = Column( String, nullable=False)
#
#
# class User(Base):
#     __tablename__ = 'test_users'
#
#     id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
#     name = Column(String, nullable=False)
#     email = Column(String, nullable=False)
#     friend = relationship('friend',backref="test_friend")


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Parent(Base):
    __tablename__ = 'parent_o2o'
    id = Column(Integer, primary_key=True,comment='test-test-test')

    # one-to-many collection
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = 'child_o2o'
    id = Column(Integer, primary_key=True,comment='child_pk_test')
    parent_id = Column(Integer, ForeignKey('parent_o2o.id'),info=({'description':'child_parent_id_test'}))

    # many-to-one scalar
    parent = relationship("Parent", back_populates="children")

crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"]
                                       )

# crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
#                                                           db_model=association_table_second,
#                                                           prefix="/association_table_second",
#                                                           tags=["association_table_second"]
#                                                           )
#
# crud_route_child_second = crud_router_builder(db_session=get_transaction_session,
#                                               db_model=Child,
#                                               prefix="/child_second",
#                                               tags=["child_second"]
#                                               )


crud_route_parent = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"]
                                        )
# crud_route_association = crud_router_builder(db_session=get_transaction_session,
#                                              db_model=association_table,
#                                              prefix="/association",
#                                              tags=["association"]
#                                              )

[app.include_router(i) for i in [crud_route_parent, crud_route_child]]

uvicorn.run(app, host="0.0.0.0", port=8001, debug=False)
