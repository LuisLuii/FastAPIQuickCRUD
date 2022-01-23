import uvicorn
from fastapi import FastAPI, Depends
from sqlalchemy.orm import declarative_base, sessionmaker

from fastapi_quickcrud import CrudMethods
from fastapi_quickcrud import crud_router_builder
from fastapi_quickcrud import sqlalchemy_to_pydantic
from fastapi_quickcrud.misc.memory_sql import sync_memory_db

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy import CHAR, Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata
association_table = Table('association', Base.metadata,
                          Column('left_id', ForeignKey('left.id')),
                          Column('right_id', ForeignKey('right.id'))
                          )


class Parent(Base):
    __tablename__ = 'left'
    id = Column(Integer, primary_key=True)
    children = relationship("Child",
                            secondary=association_table)


class Child(Base):
    __tablename__ = 'right'
    id = Column(Integer, primary_key=True)
    name = Column(CHAR, nullable=True)


user_model_m2m = sqlalchemy_to_pydantic(db_model=association_table,
                                        crud_methods=[
                                            CrudMethods.FIND_MANY,
                                            CrudMethods.UPSERT_ONE,
                                            CrudMethods.UPDATE_MANY,
                                            CrudMethods.DELETE_MANY,
                                            CrudMethods.PATCH_MANY,

                                        ],
                                        exclude_columns=[])

user_model_set = sqlalchemy_to_pydantic(db_model=Parent,
                                        crud_methods=[
                                            CrudMethods.FIND_MANY,
                                            CrudMethods.FIND_ONE,
                                            CrudMethods.CREATE_ONE,
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
                                              CrudMethods.CREATE_ONE,
                                              CrudMethods.PATCH_MANY,

                                          ],
                                          exclude_columns=[])

crud_route_1 = crud_router_builder(crud_models=user_model_set,
                                   db_model=Parent,
                                   prefix="/Parent",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["Parent"]
                                   )
crud_route_3 = crud_router_builder(crud_models=user_model_m2m,
                                   db_model=association_table,
                                   prefix="/Parent2child",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["m2m"]
                                   )
crud_route_2 = crud_router_builder(crud_models=friend_model_set,
                                   db_model=Child,
                                   async_mode=True,
                                   prefix="/Child",
                                   dependencies=[],
                                   tags=["Child"]
                                   )
post_model = friend_model_set.POST[CrudMethods.CREATE_ONE]

sync_memory_db.create_memory_table(Child)
@app.post("/hello",
           status_code=201,
          tags=["Child"],
           response_model=post_model.responseModel,
           dependencies=[])
async def my_api(
        body: post_model.requestBodyModel = Depends(post_model.requestBodyModel),
        session=Depends(sync_memory_db.get_memory_db_session)
):
    db_item = Child(**body.__dict__)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item.__dict__


app.include_router(crud_route_1)
app.include_router(crud_route_2)
app.include_router(crud_route_3)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
