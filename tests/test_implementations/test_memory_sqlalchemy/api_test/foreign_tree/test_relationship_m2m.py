from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    ForeignKey, Table, CHAR
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
                                        foreign_include=[Child, ],
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
from starlette.testclient import TestClient

[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child, crud_route_parent2,
  crud_route_association]]

client = TestClient(app)


def test_get_one_1():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }
    test_api_1 = "/parent/0/test_right/0?child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_2 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_3 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In&join_foreign_table=test_left"
    test_api_4 = "parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=child1&child____list_____comparison_operator=In&child____list=child1"
    test_api_5 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=In"
    test_api_6 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=Equal&child____list=child1"
    test_api_7 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=In&child____list=child1"
    test_api_8 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=In&child____list=child1&join_foreign_table=test_left"
    test_api_9 = "parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=Not_in&child____list=child1"
    test_api_10 = "/parent/1/test_right/1?child____str_____matching_pattern=case_sensitive&child____str=%25child%25&child____list_____comparison_operator=Not_equal&child____list=child1"
    test_api_11 = "/parent/1/test_right/1?child____str_____matching_pattern=not_case_insensitive&child____str=child1&child____list_____comparison_operator=In"

    response = client.get(test_api_1, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_2, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1', 'id': 1}

    response = client.get(test_api_3, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1',
                               'id': 1,
                               'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}

    response = client.get(test_api_4, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1', 'id': 1}

    response = client.get(test_api_5, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1', 'id': 1}

    response = client.get(test_api_6, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1', 'id': 1}

    response = client.get(test_api_7, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1', 'id': 1}

    response = client.get(test_api_8, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child': 'child1',
                               'id': 1,
                               'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}

    response = client.get(test_api_9, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_10, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_11, headers=headers)
    assert response.status_code == 404


def test_get_one_2():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }
    test_api_1 = "/parent/0/test_right_second/0?child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_2 = "/parent/1/test_right_second/1"
    test_api_3 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In&join_foreign_table=test_left"
    test_api_4 = "parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=child_second1&child_second____list_____comparison_operator=In&child_second____list=child_second1"
    test_api_5 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=In"
    test_api_6 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=Equal&child_second____list=child_second1"
    test_api_7 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=In&child_second____list=child_second1"
    test_api_8 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=In&child_second____list=child_second1&join_foreign_table=test_left"
    test_api_9 = "parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=Not_in&child_second____list=child_second1"
    test_api_10 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=case_sensitive&child_second____str=%25child_second%25&child_second____list_____comparison_operator=Not_equal&child_second____list=child_second1"
    test_api_11 = "/parent/1/test_right_second/1?child_second____str_____matching_pattern=not_case_insensitive&child_second____str=child_second1&child_second____list_____comparison_operator=In"

    response = client.get(test_api_1, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_2, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1', 'id': 1}

    response = client.get(test_api_3, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1',
                               'id': 1,
                               'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}

    response = client.get(test_api_4, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1', 'id': 1}

    response = client.get(test_api_5, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1', 'id': 1}

    response = client.get(test_api_6, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1', 'id': 1}

    response = client.get(test_api_7, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1', 'id': 1}

    response = client.get(test_api_8, headers=headers)
    assert response.status_code == 200
    assert response.json() == {'child_second': 'child_second1',
                               'id': 1,
                               'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}

    response = client.get(test_api_9, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_10, headers=headers)
    assert response.status_code == 404

    response = client.get(test_api_11, headers=headers)
    assert response.status_code == 404


def test_get_many_1():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }
    test_api_1 = "/parent/0/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_2 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_3 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____from=1&id____to=2&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_4 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____from=8&id____to=9&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_5 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&id____list=0&id____list=1&id____list=2&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In"
    test_api_6 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____str=child1&child____list_____comparison_operator=In"
    test_api_7 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____str=child%25&child____list_____comparison_operator=In"
    test_api_8 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In&child____list=child2"
    test_api_9 = "/parent/1/test_right?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child____str_____matching_pattern=case_sensitive&child____list_____comparison_operator=In&join_foreign_table=test_left"
    response = client.get(test_api_1, headers=headers)
    assert response.status_code == 204

    response = client.get(test_api_2, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1', 'id': 1},
                               {'child': 'child2', 'id': 2},
                               {'child': 'child3', 'id': 3},
                               {'child': 'child4', 'id': 4}]

    response = client.get(test_api_3, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1', 'id': 1}, {'child': 'child2', 'id': 2}]

    response = client.get(test_api_4, headers=headers)
    assert response.status_code == 204

    response = client.get(test_api_5, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1', 'id': 1}, {'child': 'child2', 'id': 2}]

    response = client.get(test_api_6, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1', 'id': 1}]

    response = client.get(test_api_7, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1', 'id': 1},
                               {'child': 'child2', 'id': 2},
                               {'child': 'child3', 'id': 3},
                               {'child': 'child4', 'id': 4}]

    response = client.get(test_api_8, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child2', 'id': 2}]

    response = client.get(test_api_9, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child': 'child1',
                                'id': 1,
                                'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}]


def test_get_many_2():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }
    test_api_1 = "/parent/0/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_2 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_3 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____from=1&id____to=2&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_4 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____from=8&id____to=9&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_5 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&id____list=0&id____list=1&id____list=2&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In"
    test_api_6 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____str=child_second1&child_second____list_____comparison_operator=In"
    test_api_7 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____str=child_second%25&child_second____list_____comparison_operator=In"
    test_api_8 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In&child_second____list=child_second2"
    test_api_9 = "/parent/1/test_right_second?id____from_____comparison_operator=Greater_than_or_equal_to&id____to_____comparison_operator=Less_than_or_equal_to&id____list_____comparison_operator=In&child_second____str_____matching_pattern=case_sensitive&child_second____list_____comparison_operator=In&join_foreign_table=test_left"
    response = client.get(test_api_1, headers=headers)
    assert response.status_code == 204

    response = client.get(test_api_2, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1', 'id': 1},
                               {'child_second': 'child_second2', 'id': 2},
                               {'child_second': 'child_second3', 'id': 3},
                               {'child_second': 'child_second4', 'id': 4}]

    response = client.get(test_api_3, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1', 'id': 1}, {'child_second': 'child_second2', 'id': 2}]

    response = client.get(test_api_4, headers=headers)
    assert response.status_code == 204

    response = client.get(test_api_5, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1', 'id': 1}, {'child_second': 'child_second2', 'id': 2}]

    response = client.get(test_api_6, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1', 'id': 1}]

    response = client.get(test_api_7, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1', 'id': 1},
                               {'child_second': 'child_second2', 'id': 2},
                               {'child_second': 'child_second3', 'id': 3},
                               {'child_second': 'child_second4', 'id': 4}]

    response = client.get(test_api_8, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second2', 'id': 2}]

    response = client.get(test_api_9, headers=headers)
    assert response.status_code == 200
    assert response.json() == [{'child_second': 'child_second1',
                                'id': 1,
                                'test_left_foreign': [{'id': 1, 'parent': 'parent1'}]}]


def setup_module(module):
    Child.__table__.create(module.engine, checkfirst=True)
    ChildSecond.__table__.create(module.engine, checkfirst=True)
    Parent.__table__.create(module.engine, checkfirst=True)
    association_table.create(module.engine, checkfirst=True)
    association_table_second.create(module.engine, checkfirst=True)
    db = module.session()

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


def teardown_module(module):
    association_table.drop(engine, checkfirst=True)
    association_table_second.drop(engine, checkfirst=True)
    ChildSecond.__table__.drop(engine, checkfirst=True)
    Parent.__table__.drop(engine, checkfirst=True)
    Child.__table__.drop(engine, checkfirst=True)
