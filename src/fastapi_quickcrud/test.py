from fastapi import FastAPI
from sqlalchemy import *
from sqlalchemy.orm import *
from fastapi_quickcrud.crud_router import generic_sql_crud_router_builder, crud_router_builder

Base = declarative_base()
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


class Parent(Base):
    __tablename__ = 'test_left'
    id = Column(Integer, primary_key=True)
    children = relationship("Child",
                            secondary=association_table)
    children_second = relationship("ChildSecond",
                                   secondary=association_table_second)


class ChildSecond(Base):
    __tablename__ = 'test_right_second'
    id = Column(Integer, primary_key=True)


crud_route_child = crud_router_builder(
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"],

                                       )

crud_route_association_table_second = crud_router_builder(
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"],

                                                          )

crud_route_child_second = crud_router_builder(
                                              db_model=Child,
                                              prefix="/child_second",
                                              tags=["child_second"],

                                              )

crud_route_parent = crud_router_builder(
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"],

                                        )
crud_route_association = crud_router_builder(
                                             db_model=association_table,
                                             prefix="/association",
                                             tags=["association"],

                                             )

app = FastAPI()
[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child,
  crud_route_association]]

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
