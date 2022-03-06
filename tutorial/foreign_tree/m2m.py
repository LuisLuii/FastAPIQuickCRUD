from fastapi import FastAPI
from fastapi_quickcrud import crud_router_builder
from sqlalchemy import *
from sqlalchemy.orm import *

from fastapi_quickcrud.misc.type import SqlType

Base = declarative_base()

from sqlalchemy.pool import StaticPool

engine = create_engine('sqlite://', echo=True,
                       connect_args={"check_same_thread": False}, pool_recycle=7200, poolclass=StaticPool)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_transaction_session():
    try:
        db = session()
        yield db
    finally:
        db.close()


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

                                       )

crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"],
                                                          sql_type=SqlType.sqlite,

                                                          )
crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"],
                                                          sql_type=SqlType.sqlite,

                                                          )

crud_route_child_second = crud_router_builder(db_session=get_transaction_session,
                                              db_model=Child,
                                              prefix="/child_second",
                                              tags=["child_second"],
                                              sql_type=SqlType.sqlite,

                                              )

crud_route_parent = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"],
                                        foreign_include=[Child,],
                                        sql_type=SqlType.sqlite,

                                        )
crud_route_parent2 = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"],
                                        foreign_include=[ChildSecond],
                                        sql_type=SqlType.sqlite,

                                        )
crud_route_association = crud_router_builder(db_session=get_transaction_session,
                                             db_model=association_table,
                                             prefix="/association",
                                             tags=["association"],
                                             sql_type=SqlType.sqlite,

                                             )
app = FastAPI()

[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child,crud_route_parent2,
  crud_route_association]]

Child.__table__.create(engine, checkfirst=True)
ChildSecond.__table__.create(engine, checkfirst=True)
Parent.__table__.create(engine, checkfirst=True)
association_table.create(engine, checkfirst=True)
association_table_second.create(engine, checkfirst=True)
db = session()
db.add(Child(id=1, child="child1"))
db.add(Child(id=2, child="child2"))
db.add(Child(id=3, child="child3"))
db.add(Child(id=4, child="child4"))
db.flush()

db.add(Parent(id=1, parent="parent1"))
db.add(Parent(id=2, parent="parent2"))
db.add(Parent(id=3, parent="parent3"))
db.add(Parent(id=4, parent="parent4"))
db.flush()
db.execute(association_table.insert().values(left_id=1, right_id=1))
db.execute(association_table.insert().values(left_id=2, right_id=2))
db.execute(association_table.insert().values(left_id=3, right_id=3))
db.execute(association_table.insert().values(left_id=4, right_id=4))

db.add(ChildSecond(id=1, child_second="child_second1"))
db.add(ChildSecond(id=2, child_second="child_second2"))
db.add(ChildSecond(id=3, child_second="child_second3"))
db.add(ChildSecond(id=4, child_second="child_second4"))
db.flush()

db.execute(association_table_second.insert().values(left_id_second=1, right_id_second=1))
db.execute(association_table_second.insert().values(left_id_second=2, right_id_second=2))
db.execute(association_table_second.insert().values(left_id_second=3, right_id_second=3))
db.execute(association_table_second.insert().values(left_id_second=4, right_id_second=4))
q = db.execute('''
                    SELECT 
        name
    FROM 
        sqlite_master 
                    ''')

available_tables = q.fetchall()
db.commit()

import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
