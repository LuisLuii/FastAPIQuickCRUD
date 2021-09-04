import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

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
    parent = relationship("Parent",
                          secondary=association_table,
                          back_populates="children")


class ChildSecond(Base):
    __tablename__ = 'test_right_second'
    id = Column(Integer, primary_key=True)
    parent_second = relationship("Parent",
                                 secondary=association_table_second,
                                 back_populates="children_second")


class Parent(Base):
    __tablename__ = 'test_left'
    id = Column(Integer, primary_key=True)
    children = relationship("Child",
                            secondary=association_table,
                            back_populates="parent")
    children_second = relationship("ChildSecond",
                                   secondary=association_table_second,
                                   back_populates="parent_second")


crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"]
                                                          )

crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"]
                                       )

crud_route_child_second = crud_router_builder(db_session=get_transaction_session,
                                              db_model=ChildSecond,
                                              prefix="/child_second",
                                              tags=["child_second"]
                                              )

crud_route_parent = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"]
                                        )
crud_route_association = crud_router_builder(db_session=get_transaction_session,
                                             db_model=association_table,
                                             prefix="/association",
                                             tags=["association"]
                                             )

app.include_router(crud_route_child)
app.include_router(crud_route_association)
app.include_router(crud_route_parent)
app.include_router(crud_route_association_table_second)
app.include_router(crud_route_child_second)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
