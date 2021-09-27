from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, text, PrimaryKeyConstraint, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, synonym

from src.fastapi_quickcrud.misc.utils import table_to_declarative_base
from src.fastapi_quickcrud import sqlalchemy_to_pydantic, CrudMethods
from src.fastapi_quickcrud.misc.exceptions import SchemaException, ColumnTypeNotSupportedException, PrimaryMissing

Base = declarative_base()

metadata = Base.metadata
UntitledTable256 = Table(
    'test_table', metadata,
    Column('char_value', CHAR(10)),
    Column('date_value', Date, server_default=text("now()")),
    Column('float4_value', Float, nullable=False),
    Column('float8_value', Float(53), nullable=False, server_default=text("10.10")),
    Column('int2_value', SmallInteger, nullable=False),
    Column('int4_value', Integer, nullable=False),
    Column('int8_value', BigInteger, server_default=text("99")),
    Column('interval_value', INTERVAL, unique=True),
    Column('json_value', JSON, unique=True),
    Column('jsonb_value', JSONB(astext_type=Text())),
    Column('numeric_value', Numeric, unique=True),
    Column('text_value', Text),
    Column('time_value', Time),
    Column('timestamp_value', DateTime),
    Column('timestamptz_value', DateTime(True)),
    Column('timetz_value', Time(True)),
    Column('uuid_value', UUID),
    Column('varchar_value', String),
    Column('array_value', ARRAY(Integer())),
    Column('array_str__value', ARRAY(String())),
)
UntitledTable256 = table_to_declarative_base(UntitledTable256)

try:
    UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                                   crud_methods=[
                                                       CrudMethods.PATCH_ONE,
                                                   ],
                                                   exclude_columns=['xml_value', 'box_valaue'])
except SchemaException as e:
    assert 'nly support one unique constraint/ Use unique constraint and composite unique constraint at same time is not supported / Use  composite unique constraint if there are more than one unique constraint' in str(e)

