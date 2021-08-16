import uuid
from typing import Optional

import uvicorn
from fastapi import FastAPI, Depends, Security, Request
from fastapi.security import HTTPBearer, APIKeyHeader, APIKeyQuery
from sqlalchemy import TypeDecorator, Table, ForeignKey
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym
from sqlalchemy.sql.sqltypes import NullType

from fastapi_quickcrud import crud_router
from fastapi_quickcrud import CrudService
from fastapi_quickcrud import CrudMethods as CrudRouter
from fastapi_quickcrud import sqlalchemy_to_pydantic
app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:1234@127.0.0.1:5432/postgres', future=True, echo=True,
                       pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
async_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_transaction_session():
    try:
        db = async_session()
        yield db
    finally:
        db.close()

class ExampleTable(Base):
    __tablename__ = 'example_table'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )
    id = Column(Integer, primary_key=True, info={'alias_name': 'primary_key'},
                server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
    primary_key = synonym('id')
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float, nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, info={'alias_name': 'int4_alias'}, nullable=False)
    int4_alias = synonym('int4_value')
    int8_value = Column(BigInteger, server_default=text("99"))
    interval_value = Column(INTERVAL)
    json_value = Column(JSON)
    jsonb_value = Column(JSONB(astext_type=Text()))
    numeric_value = Column(Numeric)
    text_value = Column(Text, info={'alias_name': 'text_alias'})
    text_alias = synonym('text_value')
    time_value = Column(Time)
    timestamp_value = Column(DateTime)
    timestamptz_value = Column(DateTime(True))
    timetz_value = Column(Time(True))
    uuid_value = Column(UUID(as_uuid=True))
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))





UntitledTable256_service = CrudService(model=ExampleTable)

UntitledTable256Model = sqlalchemy_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

UntitledTable256Model = sqlalchemy_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_MANY
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

upsert_many_router = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/upsert_many",
                          tags=["test"]
                          )
UntitledTable256Model = sqlalchemy_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.POST_REDIRECT_GET
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

post_redirect_get_router = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/post_redirect_get",
                          tags=["test"]
                          )

example_table_full_api = sqlalchemy_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.FIND_MANY,
                                                   CrudRouter.FIND_ONE,
                                                   CrudRouter.UPSERT_ONE,
                                                   CrudRouter.UPDATE_MANY,
                                                   CrudRouter.UPDATE_ONE,
                                                   CrudRouter.DELETE_ONE,
                                                   CrudRouter.DELETE_MANY,
                                                   CrudRouter.PATCH_MANY,
                                                   CrudRouter.PATCH_ONE,

                                               ],
                                               exclude_columns=['array_str__value','bytea_value', 'xml_value', 'box_valaue'])




example_table_full_router = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=example_table_full_api,
                            dependencies= [],
                          prefix="/test_CRUD",
                          tags=["test"]
                          )



ExampleTable.__table__.create(engine, checkfirst=True)
[app.include_router(i) for i in [example_table_full_router,post_redirect_get_router,upsert_many_router]]
uvicorn.run(app, host="0.0.0.0", port=8001, debug=False)


