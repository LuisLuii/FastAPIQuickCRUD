
import uuid
from typing import Optional

from guid import GUID
import uvicorn
from fastapi import FastAPI
from sqlalchemy import UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym
from sqlalchemy.sql.sqltypes import NullType

from quick_crud.misc.exceptions import MultipleSingleUniqueNotSupportedException, \
    MultiplePrimaryKeyNotSupportedException, CompositePrimaryKeyConstraintNotSupportedException, \
    ColumnTypeNotSupportedException
from quick_crud.misc.type import CrudMethods
from quick_crud.misc.utils import sqlalchemy_to_pydantic



def test_multiple_unique_but_dont_use_composite_unique_constraint():
    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        # __table_args__ = (
        #     UniqueConstraint('id', 'int4_value', 'float4_value'),
        # )
        id = Column(Integer, primary_key=True, unique=True, info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean, nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False, unique=True)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, unique=True)
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
    except MultipleSingleUniqueNotSupportedException as e:
        return
    assert False

def test_use_multiple_unique_and_composite_unique_constraint_at_same_time():
    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        __table_args__ = (
            UniqueConstraint('interval_value', 'json_value'),
        )
        id = Column(Integer, primary_key=True, unique=True, info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean, nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False, unique=True)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, unique=True)
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
    except MultipleSingleUniqueNotSupportedException as e:
        return
    assert False

def test_multiple_single_primary_key():

    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        # __table_args__ = (
        #     UniqueConstraint('id', 'int4_value', 'float4_value'),
        # )
        id = Column(Integer, primary_key=True, unique=True, info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean, primary_key=True, nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary, primary_key=True)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False, unique=True)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, unique=True)
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
    except MultiplePrimaryKeyNotSupportedException as e:
        return
    assert False

def test_use_composite_primar_key_constraint():
    '''
    __table_args__ = (
        PrimaryKeyConstraint(field2, field1),
        {},
    )
    '''
    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        __table_args__ = (
            PrimaryKeyConstraint('id', 'bool_value', 'bytea_value'),
        )
        id = Column(Integer,  unique=True, info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean,  nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False, unique=True)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, unique=True)
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
    except CompositePrimaryKeyConstraintNotSupportedException as e:
        return
    assert False

def test_use_composite_primar_key_constraint_and_multiple_single_primary_key():
    '''
    __table_args__ = (
        PrimaryKeyConstraint(field2, field1),
        {},
    )
    '''
    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        __table_args__ = (
            PrimaryKeyConstraint('id', 'bool_value', 'bytea_value'),
        )
        id = Column(Integer,  unique=True, info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean,  nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False, unique=True)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, unique=True)
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
    except CompositePrimaryKeyConstraintNotSupportedException as e:
        return
    assert False

def test_useing_not_supported_type():


    Base = declarative_base()

    class UntitledTable256(Base):
        __tablename__ = 'untitled_table_256'
        __table_args__ = (
            UniqueConstraint('id', 'int4_value', 'float4_value'),
        )
        id = Column(Integer, primary_key=True,info={'alias_name': 'primary_key'},
                    server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        primary_key = synonym('id')
        bool_value = Column(Boolean, nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False, )
        int8_value = Column(BigInteger, server_default=text("99"))
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        xml_value = Column(NullType)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))
        box_value = Column(NullType)
    # Test NullType

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['xml_value', 'box_valaue'])
        assert False
    except ColumnTypeNotSupportedException as e:
        pass
    except Exception as e:
        assert False

    # Test BLOB type

    try:
        test_model = sqlalchemy_to_pydantic(UntitledTable256, crud_methods=[
            CrudMethods.UPSERT_MANY,
        ], exclude_columns=['bytea_value'])
        assert False
    except ColumnTypeNotSupportedException as e:
        pass
    except Exception as e:
        assert False


test_use_multiple_unique_and_composite_unique_constraint_at_same_time()