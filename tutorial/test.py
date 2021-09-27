import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey, orm
from fastapi_quickcrud import crud_router_builder

Base = orm.declarative_base()


class User(Base):
    __tablename__ = 'test_users'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


friend = Table(
    'test_friend', Base.metadata,
    Column('id', ForeignKey('test_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend_name', String, nullable=False)
)

crud_route_1 = crud_router_builder(db_model=User,
                                   prefix="/user",
                                   tags=["User"],
                                   async_mode=True
                                   )
crud_route_2 = crud_router_builder(db_model=friend,
                                   prefix="/friend",
                                   tags=["friend"],
                                   async_mode=True
                                   )

app = FastAPI()
app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
