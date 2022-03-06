import json

from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    ForeignKey, Table, String
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from src.fastapi_quickcrud.misc.type import SqlType
from src.fastapi_quickcrud.crud_router import crud_router_builder

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy import create_engine

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

crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                       db_model=User,
                                   prefix="/user",
                                   tags=["User"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                       db_model=friend,
                                   prefix="/friend",
                                   tags=["friend"]
                                   )

from starlette.testclient import TestClient

[app.include_router(i) for i in
 [crud_route_1,crud_route_2]]

client = TestClient(app)


def test_():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }
    data = '[{"id": 1,"name": "string","email": "string"}]'
    response = client.post('/user', headers=headers, data=data)
    assert response.status_code == 201
    assert response.json() == [{"id": 1,"name": "string","email": "string"}]


    data  =' [{"id": 1,"friend_name": "string"}]'
    response = client.post('/friend', headers=headers, data = data)
    assert response.status_code == 201
    assert response.json() == [
  {
    "id": 1,
    "friend_name": "string"
  }
]

    response = client.get('/friend?join_foreign_table=test_users', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
  {
    "test_users_foreign": [
      {
        "id": 1,
        "name": "string",
        "email": "string"
      }
    ],
    "id": 1,
    "friend_name": "string"
  }
]



def setup_module(module):
    User.__table__.create(module.engine, checkfirst=True)
    friend.create(module.engine, checkfirst=True)


def teardown_module(module):
    friend.drop(engine, checkfirst=True)
    User.__table__.drop(engine, checkfirst=True)
