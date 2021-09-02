import json
import os

from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from src.fastapi_quickcrud.crud_router import crud_router_builder

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:1234@127.0.0.1:5432/postgres')

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy import create_engine

engine = create_engine(TEST_DATABASE_URL, future=True, echo=True,
                       pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_transaction_session():
    try:
        db = session()
        yield db
    finally:
        db.close()
class Parent(Base):
    __tablename__ = 'parent'
    id = Column(Integer, primary_key=True)
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = 'child'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent.id'))
    parent = relationship("Parent", back_populates="children")

crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"]
                                       )

crud_route_parent = crud_router_builder(db_session=get_transaction_session,
                                        db_model=Parent,
                                        prefix="/parent",
                                        tags=["parent"]
                                        )
from starlette.testclient import TestClient
[app.include_router(i) for i in [crud_route_parent, crud_route_child]]

client = TestClient(app)


def test_get_many_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/parent?join_foreign_table=child', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "id_foreign": [
                {
                    "id": 1,
                    "parent_id": 1
                },
                {
                    "id": 2,
                    "parent_id": 1
                }
            ],
            "id": 1
        },
        {
            "id_foreign": [
                {
                    "id": 3,
                    "parent_id": 2
                },
                {
                    "id": 4,
                    "parent_id": 2
                }
            ],
            "id": 2
        }
    ]


def test_get_many_without_join():
    query = {"join_foreign_table": "child"}
    data = json.dumps(query)
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/parent', headers=headers, data=data)
    assert response.status_code == 200
    print(response.json() )
    assert response.json() == [
        {
            "id": 1
        },
        {
            "id": 2
        }
    ]


def setup_module(module):
    Base.metadata.create_all

    db = session()

    db.add(Parent(id=1))
    db.add(Parent(id=2))
    db.flush()
    db.add(Child(id=1, parent_id=1))
    db.add(Child(id=2, parent_id=1))
    db.add(Child(id=3, parent_id=2))
    db.add(Child(id=4, parent_id=2))

    db.commit()

def teardown_module(module):
    Base.metadata.drop_all
