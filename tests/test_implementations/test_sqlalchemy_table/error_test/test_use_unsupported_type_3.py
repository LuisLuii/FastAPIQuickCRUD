import os

from sqlalchemy import ARRAY, BigInteger, Table, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text, PrimaryKeyConstraint, \
    create_engine
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym

from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_to_pydantic, CrudMethods, sqlalchemy_to_pydantic
from src.fastapi_quickcrud.misc.exceptions import SchemaException, MultipleSingleUniqueNotSupportedException, \
    ColumnTypeNotSupportedException

Base = declarative_base()

metadata = Base.metadata
UntitledTable256 = Table(
    'test_table', metadata,
    Column('primary_key', JSON,nullable=False,autoincrement=True,info={'alias_name': 'primary_key'}),
    Column('bool_value', Boolean, nullable=False, server_default=text("false")),
    Column('bytea_value', LargeBinary),
    Column('char_value', CHAR(10)),
    Column('date_value', Date, server_default=text("now()")),
    Column('float4_value', Float, nullable=False),
    Column('float8_value', Float(53), nullable=False, server_default=text("10.10")),
    Column('int2_value', SmallInteger, nullable=False),
    Column('int4_value', Integer, nullable=False),
    Column('int8_value', BigInteger, server_default=text("99")),
    Column('interval_value', INTERVAL),
    Column('json_value', JSON),
    Column('jsonb_value', JSONB(astext_type=Text())),
    Column('numeric_value', Numeric),
    Column('text_value', Text, unique=True),
    Column('time_value', Time),
    Column('timestamp_value', DateTime),
    Column('timestamptz_value', DateTime(True)),
    Column('timetz_value', Time(True)),
    Column('uuid_value', UUID),
    Column('varchar_value', String),
    Column('array_value', ARRAY(Integer())),
    Column('array_str__value', ARRAY(String())),

)

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_ASYNC_URL',
                                   'postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres')

engine = create_engine(TEST_DATABASE_URL, future=True, echo=True,
                       pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_transaction_session():
    try:
        db = session()
        yield db
    finally:
        db.close()

try:

    crud_route_child = crud_router_builder(db_session=get_transaction_session,
                                           db_model=UntitledTable256,
                                           prefix="/child",
                                           tags=["child"],
                                                       crud_methods=[
                                                           CrudMethods.UPSERT_MANY,
                                                       ],
                                                       exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
except ColumnTypeNotSupportedException as e:
    'not supported yet' in str(e)
