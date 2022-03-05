from fastapi import FastAPI
from fastapi_quickcrud import crud_router_builder
from sqlalchemy import *
from sqlalchemy.orm import *

Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('left_id', ForeignKey('left.id'), primary_key=True),
    Column('right_id', ForeignKey('right.id'), primary_key=True)
)

class Parent(Base):
    __tablename__ = 'left'
    id = Column(Integer, primary_key=True)
    children = relationship(
        "Child",
        secondary=association_table,
        back_populates="parents")

class Child(Base):
    __tablename__ = 'right'
    id = Column(Integer, primary_key=True)
    parents = relationship(
        "Parent",
        secondary=association_table,
        back_populates="children")

crud_route_1 = crud_router_builder(db_model=Parent,
                                   prefix="/parent",
                                   tags=["Parent"],
                                   foreign_include=[Child]
                                   )
crud_route_2 = crud_router_builder(db_model=Child,
                                   prefix="/child",
                                   tags=["Child"],
                                   foreign_include=[Parent]
                                   )
app = FastAPI()
[app.include_router(i) for i in [crud_route_1, crud_route_2]]


import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
