from datetime import datetime

import uvicorn
from fastapi import FastAPI
from sqlalchemy import create_engine, Column, types, select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, text, PrimaryKeyConstraint, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, synonym

from fastapi_quickcrud import crud_router_builder
from fastapi_quickcrud.misc.utils import table_to_declarative_base
from src.fastapi_quickcrud import sqlalchemy_to_pydantic, CrudMethods
from src.fastapi_quickcrud.misc.exceptions import SchemaException, ColumnTypeNotSupportedException, PrimaryMissing

from fastapi_quickcrud.misc.utils import table_to_declarative_base

engine = create_engine("mysql+pymysql://sql6440173:BCeFU1Plaq@sql6.freemysqlhosting.net:3306/sql6440173")

Base = declarative_base()
session = scoped_session(sessionmaker(bind=engine))



metadata = Base.metadata

UntitledTable256 = Table(
    'test_table', metadata,
    Column('primary_key', Integer, primary_key=True, nullable=False,autoincrement=True,info={'alias_name': 'primary_key'}),
    Column('bool_value', Boolean, nullable=False, server_default=text("false")),
    Column('char_value', CHAR(10)),
    Column('date_value', Date,  default=datetime.now()),
    Column('float4_value', Float, nullable=False),
    Column('float8_value', Float(53), nullable=False,  default=10.10),
    Column('int2_value', SmallInteger, nullable=False),
    Column('int4_value', Integer, nullable=False),
    Column('int8_value', BigInteger, default=99),
    Column('numeric_value', Numeric),
    Column('text_value', Text),
    Column('time_value', Time),
    Column('timestamp_value', DateTime),
    Column('timestamptz_value', DateTime(True)),
    Column('timetz_value', Time(True)),
    Column('varchar_value', String(100)),
    UniqueConstraint('primary_key', 'int4_value', 'float4_value'),
)


def get_transaction_session():
    try:
        db = session()
        yield db
    finally:
        db.close()

crud_route_association = crud_router_builder(db_session = get_transaction_session,
                                             db_model=UntitledTable256,
                                             prefix="/association",
                                             tags=["association"]
                                             )

UntitledTable256.create(engine, checkfirst=True)

app = FastAPI()

[app.include_router(i) for i in
 [crud_route_association]]
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)


