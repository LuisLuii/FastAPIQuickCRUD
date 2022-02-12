from fastapi import FastAPI
from sqlalchemy import *
from sqlalchemy.orm import *
from fastapi_quickcrud.crud_router import generic_sql_crud_router_builder

Base = declarative_base()
class Parent(Base):
    __tablename__ = 'parent_o2o'
    id = Column(Integer, primary_key=True, comment='test-test-test')
    name = Column(String, default='ok', unique = True)
    children = relationship("Child", back_populates="parent")



class Child(Base):
    __tablename__ = 'child_o2o'
    id = Column(Integer, primary_key=True, comment='child_pk_test')
    parent_id = Column(Integer, ForeignKey('parent_o2o.id'), info=({'description': 'child_parent_id_test'}))
    parent = relationship("Parent", back_populates="children")


crud_route_parent = generic_sql_crud_router_builder(
    db_model=Parent,
    prefix="/parent",
    tags=["parent"],
)

crud_route_child = generic_sql_crud_router_builder(
    db_model=Child,
    prefix="/child",
    tags=["child"]
)

app = FastAPI()
[app.include_router(i) for i in [crud_route_parent, crud_route_child]]

@app.get("/", tags=["child"])
async def root():
    return {"message": "Hello World"}

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
