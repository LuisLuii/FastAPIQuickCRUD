import os

from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    ForeignKey, Table
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


crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                       db_model=Child,
                                       prefix="/child",
                                       tags=["child"]
                                       )

crud_route_association_table_second = crud_router_builder(db_session=get_transaction_session,
                                                          db_model=association_table_second,
                                                          prefix="/association_table_second",
                                                          tags=["association_table_second"]
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
from starlette.testclient import TestClient

[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child,
  crud_route_association]]

client = TestClient(app)


def test_get_parent_many_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/parent?join_foreign_table=test_right', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_right_foreign": [
                {
                    "id": 1
                }
            ],
            "id": 1
        },
        {
            "test_right_foreign": [
                {
                    "id": 2
                }
            ],
            "id": 2
        },
        {
            "test_right_foreign": [
                {
                    "id": 3
                }
            ],
            "id": 3
        },
        {
            "test_right_foreign": [
                {
                    "id": 4
                }
            ],
            "id": 4
        }
    ]

    response = client.get('/parent/1?join_foreign_table=test_right', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
            "test_right_foreign": [
                {
                    "id": 1
                }
            ],
            "id": 1
        }

    response = client.get('/parent/1?join_foreign_table=test_right_second', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
            "test_right_second_foreign": [
                {
                    "id": 1
                }
            ],
            "id": 1
        }

    response = client.get('/parent/1?join_foreign_table=test_right&join_foreign_table=test_right_second', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
            "test_right_foreign": [
                {
                    "id": 1
                }
            ],
            "test_right_second_foreign": [
                {
                    "id": 1
                }
            ],
            "id": 1
        }


def test_get_child_many_without_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/child', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1
        },
        {
            "id": 2
        },
        {
            "id": 3
        },
        {
            "id": 4
        }
    ]


def test_get_child_many_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/child?join_foreign_table=test_left', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
  {
    "test_left_foreign": [
      {
        "id": 1
      }
    ],
    "id": 1
  },
  {
    "test_left_foreign": [
      {
        "id": 2
      }
    ],
    "id": 2
  },
  {
    "test_left_foreign": [
      {
        "id": 3
      }
    ],
    "id": 3
  },
  {
    "test_left_foreign": [
      {
        "id": 4
      }
    ],
    "id": 4
  }
]



def test_get_association_many_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/association?join_foreign_table=test_left', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_left_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id": 1,
            "right_id": 1
        },
        {
            "test_left_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id": 2,
            "right_id": 2
        },
        {
            "test_left_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id": 3,
            "right_id": 3
        },
        {
            "test_left_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id": 4,
            "right_id": 4
        }
    ]

    response = client.get('/association?join_foreign_table=test_right', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_right_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id": 1,
            "right_id": 1
        },
        {
            "test_right_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id": 2,
            "right_id": 2
        },
        {
            "test_right_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id": 3,
            "right_id": 3
        },
        {
            "test_right_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id": 4,
            "right_id": 4
        }
    ]

    response = client.get('/association?join_foreign_table=test_left&join_foreign_table=test_right', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_left_foreign": [
                {
                    "id": 1
                }
            ],
            "test_right_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id": 1,
            "right_id": 1
        },
        {
            "test_left_foreign": [
                {
                    "id": 2
                }
            ],
            "test_right_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id": 2,
            "right_id": 2
        },
        {
            "test_left_foreign": [
                {
                    "id": 3
                }
            ],
            "test_right_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id": 3,
            "right_id": 3
        },
        {
            "test_left_foreign": [
                {
                    "id": 4
                }
            ],
            "test_right_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id": 4,
            "right_id": 4
        }
    ]


def test_get_association_many_second_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/association_table_second?join_foreign_table=test_right_second', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_right_second_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id_second": 1,
            "right_id_second": 1
        },
        {
            "test_right_second_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id_second": 2,
            "right_id_second": 2
        },
        {
            "test_right_second_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id_second": 3,
            "right_id_second": 3
        },
        {
            "test_right_second_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id_second": 4,
            "right_id_second": 4
        }
    ]
    response = client.get('/association_table_second?join_foreign_table=test_left', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_left_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id_second": 1,
            "right_id_second": 1
        },
        {
            "test_left_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id_second": 2,
            "right_id_second": 2
        },
        {
            "test_left_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id_second": 3,
            "right_id_second": 3
        },
        {
            "test_left_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id_second": 4,
            "right_id_second": 4
        }
    ]

    response = client.get('/association_table_second?join_foreign_table=test_left&join_foreign_table=test_right_second',
                          headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_left_foreign": [
                {
                    "id": 1
                }
            ],
            "test_right_second_foreign": [
                {
                    "id": 1
                }
            ],
            "left_id_second": 1,
            "right_id_second": 1
        },
        {
            "test_left_foreign": [
                {
                    "id": 2
                }
            ],
            "test_right_second_foreign": [
                {
                    "id": 2
                }
            ],
            "left_id_second": 2,
            "right_id_second": 2
        },
        {
            "test_left_foreign": [
                {
                    "id": 3
                }
            ],
            "test_right_second_foreign": [
                {
                    "id": 3
                }
            ],
            "left_id_second": 3,
            "right_id_second": 3
        },
        {
            "test_left_foreign": [
                {
                    "id": 4
                }
            ],
            "test_right_second_foreign": [
                {
                    "id": 4
                }
            ],
            "left_id_second": 4,
            "right_id_second": 4
        }
    ]

    response = client.get('/association_table_second', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "left_id_second": 1,
            "right_id_second": 1
        },
        {
            "left_id_second": 2,
            "right_id_second": 2
        },
        {
            "left_id_second": 3,
            "right_id_second": 3
        },
        {
            "left_id_second": 4,
            "right_id_second": 4
        }
    ]


def test_get_child_many_second_with_join():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.get('/child_second', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1
        },
        {
            "id": 2
        },
        {
            "id": 3
        },
        {
            "id": 4
        }
    ]

    response = client.get('/child_second/1', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
            "id": 1
        }

    response = client.get('/child_second?join_foreign_table=test_left', headers=headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "test_left_foreign": [
                {
                    "id": 1
                }
            ],
            "id": 1
        },
        {
            "test_left_foreign": [
                {
                    "id": 2
                }
            ],
            "id": 2
        },
        {
            "test_left_foreign": [
                {
                    "id": 3
                }
            ],
            "id": 3
        },
        {
            "test_left_foreign": [
                {
                    "id": 4
                }
            ],
            "id": 4
        }
    ]

    response = client.get('/child_second/1?join_foreign_table=test_left', headers=headers)
    assert response.status_code == 200
    assert response.json() == {
    "test_left_foreign": [
      {
        "id": 1
      }
    ],
    "id": 1
  }


def setup_module(module):
    Child.__table__.create(engine, checkfirst=True)
    ChildSecond.__table__.create(engine, checkfirst=True)
    Parent.__table__.create(engine, checkfirst=True)
    association_table.create(engine, checkfirst=True)
    association_table_second.create(engine, checkfirst=True)
    db = session()

    db.add(Child(id=1))
    db.add(Child(id=2))
    db.add(Child(id=3))
    db.add(Child(id=4))
    db.flush()

    db.add(Parent(id=1))
    db.add(Parent(id=2))
    db.add(Parent(id=3))
    db.add(Parent(id=4))
    db.flush()
    db.execute(association_table.insert().values(left_id=1, right_id=1))
    db.execute(association_table.insert().values(left_id=2, right_id=2))
    db.execute(association_table.insert().values(left_id=3, right_id=3))
    db.execute(association_table.insert().values(left_id=4, right_id=4))

    db.add(ChildSecond(id=1))
    db.add(ChildSecond(id=2))
    db.add(ChildSecond(id=3))
    db.add(ChildSecond(id=4))
    db.flush()

    db.execute(association_table_second.insert().values(left_id_second=1, right_id_second=1))
    db.execute(association_table_second.insert().values(left_id_second=2, right_id_second=2))
    db.execute(association_table_second.insert().values(left_id_second=3, right_id_second=3))
    db.execute(association_table_second.insert().values(left_id_second=4, right_id_second=4))

    db.commit()

    print()


def teardown_module(module):
    association_table.drop(engine, checkfirst=True)
    association_table_second.drop(engine, checkfirst=True)
    ChildSecond.__table__.drop(engine, checkfirst=True)
    Parent.__table__.drop(engine, checkfirst=True)
    Child.__table__.drop(engine, checkfirst=True)
