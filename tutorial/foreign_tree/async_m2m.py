import asyncio

from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    ForeignKey, Table, CHAR
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from src.fastapi_quickcrud.misc.type import SqlType
from src.fastapi_quickcrud.crud_router import crud_router_builder

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy.pool import StaticPool

engine = create_async_engine('sqlite+aiosqlite://',
                             future=True,
                             echo=True,
                             pool_pre_ping=True,
                             pool_recycle=7200,
                             connect_args={"check_same_thread": False},
                             poolclass=StaticPool)

session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=engine,
                       class_=AsyncSession)


async def get_transaction_session():
    async with session() as s:
        yield s


association_table = Table('test_association', Base.metadata,
                          Column('left_id', ForeignKey('test_left.id')),
                          Column('right_id', ForeignKey('test_right.id'))
                          )

association_table_second = Table('test_association_second', Base.metadata,
                                 Column('left_id_second', ForeignKey('test_left.id')),
                                 Column('right_id_second', ForeignKey('test_right_second.id'))
                                 )


class Child(Base):
    __tablename__ = 'test_right'
    id = Column(Integer, primary_key=True)
    child = Column(CHAR(10))
    parent = relationship("Parent",
                          secondary=association_table)


class Parent(Base):
    __tablename__ = 'test_left'
    id = Column(Integer, primary_key=True)
    parent = Column(CHAR(10))
    children = relationship("Child",
                            secondary=association_table)
    children_second = relationship("ChildSecond",
                                   secondary=association_table_second)


class ChildSecond(Base):
    __tablename__ = 'test_right_second'
    id = Column(Integer, primary_key=True)
    child_second = Column(CHAR(10))
    children_second = relationship("Parent",
                                   secondary=association_table_second)


crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"],
                                       sql_type=SqlType.sqlite,
                                       foreign_include=[Parent],
                                       async_mode=True

                                       )

crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"],
                                                          sql_type=SqlType.sqlite,
                                                          async_mode=True

                                                          )
crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"],
                                                          sql_type=SqlType.sqlite,
                                                          async_mode=True

                                                          )

crud_route_child_second = crud_router_builder(db_session=get_transaction_session,
                                              db_model=Child,
                                              prefix="/child_second",
                                              tags=["child_second"],
                                              sql_type=SqlType.sqlite,
                                              async_mode=True

                                              )

crud_route_parent = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"],
                                        foreign_include=[Child, ],
                                        sql_type=SqlType.sqlite,
                                        async_mode=True

                                        )
crud_route_parent2 = crud_router_builder(db_session=get_transaction_session,
                                         db_model=Parent,
                                         prefix="/parent",
                                         tags=["parent"],
                                         foreign_include=[ChildSecond],
                                         sql_type=SqlType.sqlite,
                                         async_mode=True

                                         )
crud_route_association = crud_router_builder(db_session=get_transaction_session,
                                             db_model=association_table,
                                             prefix="/association",
                                             tags=["association"],
                                             sql_type=SqlType.sqlite,

                                             async_mode=True
                                             )

[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child, crud_route_parent2,
  crud_route_association]]

from starlette.testclient import TestClient


async def create_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        db = session()

        db.add(Child(id=1, child="child1"))
        db.add(Child(id=2, child="child2"))
        db.add(Child(id=3, child="child3"))
        db.add(Child(id=4, child="child4"))
        await db.flush()

        db.add(Parent(id=1, parent="parent1"))
        db.add(Parent(id=2, parent="parent2"))
        db.add(Parent(id=3, parent="parent3"))
        db.add(Parent(id=4, parent="parent4"))
        await db.flush()
        await db.execute(association_table.insert().values(left_id=1, right_id=1))
        await db.execute(association_table.insert().values(left_id=2, right_id=2))
        await db.execute(association_table.insert().values(left_id=3, right_id=3))
        await db.execute(association_table.insert().values(left_id=4, right_id=4))

        db.add(ChildSecond(id=1, child_second="child_second1"))
        db.add(ChildSecond(id=2, child_second="child_second2"))
        db.add(ChildSecond(id=3, child_second="child_second3"))
        db.add(ChildSecond(id=4, child_second="child_second4"))
        await db.flush()

        await db.execute(association_table_second.insert().values(left_id_second=1, right_id_second=1))
        await db.execute(association_table_second.insert().values(left_id_second=2, right_id_second=2))
        await db.execute(association_table_second.insert().values(left_id_second=3, right_id_second=3))
        await db.execute(association_table_second.insert().values(left_id_second=4, right_id_second=4))
        await db.commit()


loop = asyncio.get_event_loop()
loop.run_until_complete(create_table())

import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
