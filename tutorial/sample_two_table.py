import uvicorn
from fastapi import FastAPI
from sqlalchemy.orm import declarative_base, sessionmaker, synonym

from fastapi_quickcrud import crud_router_builder

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine('postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres', future=True, echo=True,
                             pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
async_session = sessionmaker(bind=engine, class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        async with session.begin():
            yield session


from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, ForeignKey, Index, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Table, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Category(Base):
    __tablename__ = 'category'

    category_id = Column(Integer, primary_key=True,
                         server_default=text("nextval('category_category_id_seq'::regclass)"))
    name = Column(String(50))

    movies = relationship('Movie', secondary='movie_category_junction')


t_critical_fault_chart = Table(
    'critical_fault_chart', metadata,
    Column('log_datetime', TIMESTAMP(True, 0)),
    Column('site_code', String),
    Column('site_name', String),
    Column('equipment_type', String(64)),
    Column('crit_fault_cnt', BigInteger)
)


class DataRestCachingCompOption(Base):
    __tablename__ = 'data_rest_caching_comp_option'

    comp_id = Column(Integer, primary_key=True,
                     server_default=text("nextval('data_rest_caching_comp_option_comp_id_seq'::regclass)"))
    comp_hash = Column(CHAR(64), nullable=False, unique=True)
    comp_content = Column(JSONB(astext_type=Text()), nullable=False)
    created_at = Column(DateTime(True), server_default=text("now()"))


class DataRestCachingFilterOption(Base):
    __tablename__ = 'data_rest_caching_filter_option'

    filter_id = Column(Integer, primary_key=True,
                       server_default=text("nextval('data_rest_caching_filter_option_filter_id_seq'::regclass)"))
    filter_hash = Column(CHAR(64), nullable=False, unique=True)
    filter_content = Column(JSONB(astext_type=Text()), nullable=False)
    created_at = Column(DateTime(True), server_default=text("now()"))


class DataRestCachingQueryOption(Base):
    __tablename__ = 'data_rest_caching_query_option'

    query_id = Column(Integer, primary_key=True,
                      server_default=text("nextval('data_rest_caching_query_option_query_id_seq'::regclass)"))
    query_hash = Column(CHAR(64), nullable=False, unique=True)
    query_content = Column(JSONB(astext_type=Text()), nullable=False)
    created_at = Column(DateTime(True), server_default=text("now()"))


t_data_rest_pre_aggregated_data_view = Table(
    'data_rest_pre_aggregated_data_view', metadata,
    Column('site_code', String(24)),
    Column('timestamp', DateTime(True)),
    Column('query_hash', CHAR(64)),
    Column('filter_hash', CHAR(64)),
    Column('comp_hash', CHAR(64)),
    Column('payload', LargeBinary),
    Column('updated_at', DateTime(True))
)

t_display_fault = Table(
    'display_fault', metadata,
    Column('log_datetime', TIMESTAMP(True, 0)),
    Column('site_name_en', String),
    Column('site_code', String),
    Column('device_name', String),
    Column('equip_type_name', String(64)),
    Column('detailed_result', JSONB(astext_type=Text())),
    Column('plot_metadata', JSONB(astext_type=Text())),
    Column('impact', JSONB(astext_type=Text()))
)

t_equipment_fault_overview = Table(
    'equipment_fault_overview', metadata,
    Column('log_datetime', TIMESTAMP(True, 0)),
    Column('site_code', String),
    Column('site_name', String),
    Column('equip_type_name', String(64)),
    Column('crit_fault_cnt', BigInteger),
    Column('minor_fault_cnt', BigInteger)
)


class EquipmentTypeNew(Base):
    __tablename__ = 'equipment_type_new'
    __table_args__ = (
        UniqueConstraint('equip_type_id', 'equip_type_name'),
    )

    equip_type_id = Column(Integer, primary_key=True, unique=True,
                           server_default=text("nextval('equipment_type_equip_type_id_seq'::regclass)"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    equip_type_name = Column(String(64), nullable=False, unique=True)


class EquipmentType(Base):
    __tablename__ = 'equipment_types'

    equip_type_id = Column(Integer, primary_key=True,
                           server_default=text("nextval('equipment_types_equip_type_id_seq'::regclass)"))
    equip_type_name = Column(String(64), nullable=False, unique=True)
    creation_time = Column(DateTime(True), server_default=text("now()"))


class Example(Base):
    __tablename__ = 'example'
    __table_args__ = (
        UniqueConstraint('p_id', 'test'),
    )

    p_id = Column(Integer, primary_key=True)
    test = Column(Integer)
    test_1 = Column(Text)


class ExampleTable(Base):
    __tablename__ = 'example_table'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    uuid_value = Column(UUID)
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


t_fault_diagnosis_view = Table(
    'fault_diagnosis_view', metadata,
    Column('log_datetime', TIMESTAMP(True, 0)),
    Column('site_code', String),
    Column('device_name', String),
    Column('detailed_result', JSONB(astext_type=Text())),
    Column('plot_metadata', JSONB(astext_type=Text())),
    Column('severity', String(16)),
    Column('equip_type_id', Integer),
    Column('equip_type_name', String(64)),
    Column('impact', JSONB(astext_type=Text()))
)

t_fault_features_view = Table(
    'fault_features_view', metadata,
    Column('log_date', Date),
    Column('site_code', String(24)),
    Column('device_name', String(64)),
    Column('feature_name', String(64)),
    Column('sub_type', String(64)),
    Column('value_json', JSONB(astext_type=Text()))
)

t_fault_list = Table(
    'fault_list', metadata,
    Column('log_datetime', DateTime(True)),
    Column('site_code', String),
    Column('site_name', String),
    Column('device_name', String),
    Column('equip_type_name', String(64)),
    Column('severity', String(16)),
    Column('impact', JSONB(astext_type=Text())),
    Column('fault_cnt', BigInteger),
    Column('detailed_result', JSONB(astext_type=Text())),
    Column('fault_category', JSONB(astext_type=Text()))
)


class FunctionGroup(Base):
    __tablename__ = 'function_group'

    func_group_id = Column(String(5), primary_key=True)
    func_group_name = Column(String, nullable=False)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    function_catagory = Column(String(20), nullable=False, server_default=text("'site'::character varying"))


t_list_of_critical_fault = Table(
    'list_of_critical_fault', metadata,
    Column('log_datetime', TIMESTAMP(True, 0)),
    Column('site_code', String),
    Column('site_name', String),
    Column('device_name', String),
    Column('severity', String(16)),
    Column('equipment_type', String(64)),
    # Column('impact', JSONB(astext_type=Text())),
    # Column('fault_issue', JSONB(astext_type=Text()))
)


class Movie(Base):
    __tablename__ = 'movie'

    movie_id = Column(Integer, primary_key=True, server_default=text("nextval('movie_movie_id_seq'::regclass)"))
    name = Column(String(50))


class ProcessedFilter(Base):
    __tablename__ = 'processed_filter'

    filter_id = Column(Integer, primary_key=True,
                       server_default=text("nextval('processed_filter_filter_id_seq'::regclass)"))
    name = Column(String, nullable=False, unique=True)


class ProcessedResolution(Base):
    __tablename__ = 'processed_resolution'

    resolution_id = Column(Integer, primary_key=True,
                           server_default=text("nextval('processed_resolution_resolution_id_seq'::regclass)"))
    name = Column(String, nullable=False, unique=True)


class ProcessedValue(Base):
    __tablename__ = 'processed_value'

    pid = Column(UUID, primary_key=True, nullable=False)
    timestamp = Column(DateTime(True), primary_key=True, nullable=False)
    count = Column(Integer, nullable=False)
    value = Column(Float(53))
    sum = Column(Float(53))
    mean = Column(Float(53))
    std = Column(Float(53))
    min = Column(Float(53))
    max = Column(Float(53))
    median = Column(Float(53))


class RefCode(Base):
    __tablename__ = 'ref_code'

    code_key = Column(String, primary_key=True, nullable=False)
    code_type = Column(String, primary_key=True, nullable=False)
    code_sub_type = Column(String, primary_key=True, nullable=False)
    descn = Column(String)
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))


class RefFilter(Base):
    __tablename__ = 'ref_filter'

    code_key = Column(String(20), primary_key=True, nullable=False)
    code_type = Column(String(20), primary_key=True, nullable=False)
    processed_filter_id = Column(SmallInteger, nullable=False)
    descn = Column(String(100))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))
    code_sub_type = Column(String(20))


class RefResolution(Base):
    __tablename__ = 'ref_resolution'

    code_key = Column(String(20), primary_key=True, nullable=False)
    code_type = Column(String(20), primary_key=True, nullable=False)
    processed_resolution_id = Column(SmallInteger, nullable=False)
    descn = Column(String(100))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))


class RefSymptomGroup(Base):
    __tablename__ = 'ref_symptom_group'

    id = Column(String(40), primary_key=True)
    description = Column(String(100))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))


class RelationshipTestA(Base):
    __tablename__ = 'relationship_test_a'

    id = Column(Integer, primary_key=True, server_default=text("nextval('untitled_table_271_id_seq'::regclass)"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


class Sometable(Base):
    __tablename__ = 'sometable'
    __table_args__ = (
        UniqueConstraint('col1', 'col2'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('sometable_id_seq'::regclass)"))
    col1 = Column(Integer, nullable=False)
    col2 = Column(Integer, nullable=False)


class TempSite(Base):
    __tablename__ = 'temp_sites'

    site_name_chn = Column(String)
    site_name_en = Column(String)
    tenant_id = Column(UUID, nullable=False)
    version = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))
    site_code = Column(String, primary_key=True)
    photo = Column(String)
    location = Column(String)
    weather_station = Column(String)
    is_activate = Column(Boolean)


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(UUID, primary_key=True)
    tenant_code = Column(String(10), nullable=False, unique=True)
    tenant_name_en = Column(String(750), server_default=text("NULL::character varying"))
    tenant_name_chn = Column(String(150), server_default=text("NULL::character varying"))
    logo = Column(String(1000), server_default=text("NULL::character varying"))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True), index=True)
    version = Column(Integer, nullable=False, server_default=text("0"))


class TestAliasUniqueColumn(Base):
    __tablename__ = 'test_alias_unique_column'
    __table_args__ = (
        UniqueConstraint('id', 'test_case_column', 'float4_value'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    test_case_column = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestAliasUniqueColumnAsync(Base):
    __tablename__ = 'test_alias_unique_column_async'
    __table_args__ = (
        UniqueConstraint('id', 'test_case_column', 'float4_value'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    test_case_column = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestBuildMyself(Base):
    __tablename__ = 'test_build_myself'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('test_build_myself_id_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    uuid_value = Column(UUID)
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestBuildMyselfAsync(Base):
    __tablename__ = 'test_build_myself_async'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('test_build_myself_async_id_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    uuid_value = Column(UUID)
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestNoAlia(Base):
    __tablename__ = 'test_no_alias'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestNoAliasAsync(Base):
    __tablename__ = 'test_no_alias_async'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestTable(Base):
    __tablename__ = 'test_table'
    __table_args__ = (
        UniqueConstraint('primary_key', 'int4_value', 'float4_value'),
    )

    primary_key = Column(Integer, primary_key=True,
                         server_default=text("nextval('test_table_primary_key_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    uuid_value = Column(UUID)
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestUuidPrimary(Base):
    __tablename__ = 'test_uuid_primary'
    __table_args__ = (
        UniqueConstraint('primary_key', 'int4_value', 'float4_value'),
    )

    primary_key = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestUuidPrimaryAsync(Base):
    __tablename__ = 'test_uuid_primary_async'
    __table_args__ = (
        UniqueConstraint('primary_key', 'int4_value', 'float4_value'),
    )

    primary_key = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


class TestUuidPrimarySync(Base):
    __tablename__ = 'test_uuid_primary_sync'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float(53), nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    varchar_value = Column(String)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))


# class UntitledTable256(Base):
#     __tablename__ = 'untitled_table_256'
#     __table_args__ = (
#         UniqueConstraint('id', 'int4_value', 'float4_value'),
#     )
#
#     id = Column(Integer, primary_key=True, nullable=False,
#                 server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
#     bool_value = Column(Boolean, primary_key=True, nullable=False, server_default=text("false"))
#     bytea_value = Column(LargeBinary)
#     char_value = Column(CHAR(10))
#     date_value = Column(Date, server_default=text("now()"))
#     float4_value = Column(Float, nullable=False)
#     float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
#     int2_value = Column(SmallInteger, nullable=False)
#     int4_value = Column(Integer, nullable=False)
#     int8_value = Column(BigInteger, server_default=text("99"))
#     interval_value = Column(INTERVAL)
#     json_value = Column(JSON)
#     jsonb_value = Column(JSONB(astext_type=Text()))
#     numeric_value = Column(Numeric)
#     text_value = Column(Text)
#     time_value = Column(Time)
#     timestamp_value = Column(DateTime)
#     timestamptz_value = Column(DateTime(True))
#     timetz_value = Column(Time(True))
#     uuid_value = Column(UUID)
#     varchar_value = Column(String)
#     xml_value = Column(NullType)
#     array_value = Column(ARRAY(Integer()))
#     array_str__value = Column(ARRAY(String()))
#     box_valaue = Column(NullType)


t_user_group_dashboard = Table(
    'user_group_dashboard', metadata,
    Column('ordering', Integer, nullable=False),
    Column('created_at', DateTime(True), nullable=False),
    Column('updated_at', DateTime(True), nullable=False),
    Column('deleted_at', DateTime(True)),
    Column('dashboard_id', UUID, nullable=False),
    Column('user_group_id', UUID, nullable=False),
    Column('tenant_id', UUID, nullable=False),
    Column('children_list', ARRAY(UUID())),
    Column('created_by', UUID),
    Column('item_type', String)
)

t_user_policy_table = Table(
    'user_policy_table', metadata,
    Column('user_group_name', String),
    Column('group_id', UUID),
    Column('policy_level', Integer),
    Column('policy_name', String),
    Column('policy_id', UUID),
    Column('site_code', String),
    Column('user_info', JSON),
    Column('available_function', JSON)
)


class ZFaultDiagnosisType(Base):
    __tablename__ = 'z_fault_diagnosis_type'

    diagnosis_type_id = Column(Integer, primary_key=True,
                               server_default=text("nextval('z_fault_diagnosis_type_diagnosis_type_id_seq'::regclass)"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    severity = Column(String(16))
    impact = Column(JSONB(astext_type=Text()))
    recommendation = Column(JSONB(astext_type=Text()))
    issue = Column(JSONB(astext_type=Text()))


class FaultFeatureTypeNew(Base):
    __tablename__ = 'fault_feature_type_new'
    __table_args__ = (
        UniqueConstraint('equip_type_id', 'feature_name', 'sub_type', 'frequency', 'attribute_name'),
    )

    feature_type_id = Column(Integer, primary_key=True,
                             server_default=text("nextval('fault_feature_type_feature_type_id_seq'::regclass)"))
    equip_type_id = Column(ForeignKey('equipment_type_new.equip_type_id'), nullable=False)
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    feature_name = Column(String(64), nullable=False)
    sub_type = Column(String(64), nullable=False)
    frequency = Column(String(16), nullable=False)
    attribute_name = Column(JSONB(astext_type=Text()), nullable=False)

    equip_type = relationship('EquipmentTypeNew')


class FaultFeatureType(Base):
    __tablename__ = 'fault_feature_types'
    __table_args__ = (
        UniqueConstraint('feature_name', 'sub_type', 'equip_type_id'),
    )

    feature_type_id = Column(Integer, primary_key=True,
                             server_default=text("nextval('fault_feature_types_feature_type_id_seq'::regclass)"))
    feature_name = Column(String(64), nullable=False)
    sub_type = Column(String(64), nullable=False)
    equip_type_id = Column(ForeignKey('equipment_types.equip_type_id'), nullable=False)
    creation_time = Column(DateTime(True), server_default=text("now()"))

    equip_type = relationship('EquipmentType')


class FaultSymptomType(Base):
    __tablename__ = 'fault_symptom_type'
    __table_args__ = (
        UniqueConstraint('equip_type_id', 'symptom_name', 'frequency', 'attribute_names'),
    )

    symptom_type_id = Column(Integer, primary_key=True,
                             server_default=text("nextval('fault_symptom_type_symptom_type_id_seq'::regclass)"))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    symptom_name = Column(String(64), nullable=False)
    frequency = Column(String(16), nullable=False)
    attribute_names = Column(String(64), nullable=False)
    equip_type_id = Column(ForeignKey('equipment_type_new.equip_type_id'), nullable=False)

    equip_type = relationship('EquipmentTypeNew')


class Function(Base):
    __tablename__ = 'functions'

    func_id = Column(String(10), primary_key=True)
    func_name = Column(String(100))
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    func_group_id = Column(ForeignKey('function_group.func_group_id'))

    func_group = relationship('FunctionGroup')


t_movie_category_junction = Table(
    'movie_category_junction', metadata,
    Column('movie_id', ForeignKey('movie.movie_id'), primary_key=True, nullable=False),
    Column('category_id', ForeignKey('category.category_id'), primary_key=True, nullable=False)
)

t_relationship_test_b = Table(
    'relationship_test_b', metadata,
    Column('id', ForeignKey('relationship_test_a.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend', String, nullable=False)
)


class Site(Base):
    __tablename__ = 'sites'

    id = Column(String(24), primary_key=True)
    site_name_chn = Column(String)
    site_name_en = Column(String)
    tenant_id = Column(ForeignKey('tenants.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=False)
    version = Column(Integer, nullable=False, server_default=text("0"))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))
    site_code = Column(String, unique=True)
    photo = Column(String)
    location = Column(String)
    weather_station = Column(String)
    is_activate = Column(Boolean)

    tenant = relationship('Tenant')


class TenantPolicy(Base):
    __tablename__ = 'tenant_policy'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(ForeignKey('tenants.id'), nullable=False)
    policy_name = Column(String, nullable=False)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    policy_level = Column(Integer, nullable=False)

    tenant = relationship('Tenant')


class UserGroup(Base):
    __tablename__ = 'user_group'

    id = Column(UUID, primary_key=True, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(ForeignKey('tenants.id', onupdate='CASCADE'), nullable=False)
    group_name = Column(String, nullable=False)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    description = Column(Text)
    policy_id = Column(UUID)
    icon_url = Column(Text)

    tenant = relationship('Tenant')


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    first_name = Column(String(30))
    last_name = Column(String(70))
    email = Column(String(100), nullable=False, unique=True)
    avatar = Column(String(1000), server_default=text("NULL::character varying"))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True), index=True)
    version = Column(Integer, nullable=False, server_default=text("0"))
    tenant_id = Column(ForeignKey('tenants.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=False, index=True)
    active = Column(Boolean, nullable=False, server_default=text("false"))

    tenant = relationship('Tenant')


class WidgetInfo(Base):
    __tablename__ = 'widget_info'

    id = Column(UUID, primary_key=True)
    method_template_id = Column(String)
    title = Column(String)
    widget_type = Column(String, nullable=False)
    tenant_id = Column(ForeignKey('tenants.id'), nullable=False)
    polling_interval = Column(Integer)
    internal_dataset = Column(JSONB(astext_type=Text()))
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    local_start_date = Column(DateTime(True))
    local_end_date = Column(DateTime(True))
    created_by = Column(UUID)
    local_filter_option = Column(JSONB(astext_type=Text()))
    local_groupby = Column(String(255))
    point_configs = Column(JSONB(astext_type=Text()))
    groupby_point_configs = Column(JSONB(astext_type=Text()))
    chart_data = Column(ARRAY(JSONB(astext_type=Text())))
    axis_config = Column(JSONB(astext_type=Text()))
    axis = Column(JSONB(astext_type=Text()))
    extra_axis = Column(JSONB(astext_type=Text()))
    legend_orientation = Column(String)
    legend_location = Column(String)
    legend = Column(JSONB(astext_type=Text()))
    color_palette = Column(ARRAY(String()))
    marker_symbol = Column(String)
    extra_axis_data = Column(ARRAY(JSONB(astext_type=Text())))
    alignment = Column(String)
    required_other_data_source = Column(Boolean)
    extra_columns = Column(ARRAY(String()))
    testing_colors = Column(JSONB(astext_type=Text()))
    subtitle = Column(String)
    desc = Column(String)
    ref_widget_data_id = Column(UUID)
    extra_rows = Column(JSONB(astext_type=Text()))
    horizontal_rows = Column(ARRAY(String()))
    model_unit = Column(String)
    chart_data_2 = Column(JSONB(astext_type=Text()))

    tenant = relationship('Tenant')


t_apikeys = Table(
    'apikeys', metadata,
    Column('user_id', ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('apikey', String, nullable=False, unique=True),
    Column('description', String),
    Column('created_at', DateTime(True), server_default=text("CURRENT_TIMESTAMP"))
)


class Dashboard(Base):
    __tablename__ = 'dashboards'

    id = Column(UUID, primary_key=True, info={'alias_name': 'primary_key'})
    icon = Column(String(1000), server_default=text("NULL::character varying"))
    name_en = Column(String(750), nullable=False)
    name_chn = Column(String(150), nullable=False)
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))
    version = Column(Integer, nullable=False, server_default=text("0"))
    tenant_id = Column(ForeignKey('tenants.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=False, index=True)
    descn_en = Column(String)
    descn_chn = Column(String)
    site_id = Column(ForeignKey('sites.id', onupdate='CASCADE'), index=True)
    compact_type = Column(String(10), server_default=text("'vertical'::character varying"))
    item_type = Column(String, nullable=False)

    site = relationship('Site')
    tenant = relationship('Tenant')


class DataRestCachingPayload(Base):
    __tablename__ = 'data_rest_caching_payload'

    site_code = Column(ForeignKey('sites.site_code', ondelete='CASCADE'), primary_key=True, nullable=False)
    timestamp = Column(DateTime(True), primary_key=True, nullable=False)
    query_id = Column(ForeignKey('data_rest_caching_query_option.query_id', ondelete='CASCADE'), primary_key=True,
                      nullable=False)
    filter_id = Column(ForeignKey('data_rest_caching_filter_option.filter_id', ondelete='CASCADE'), primary_key=True,
                       nullable=False)
    comp_id = Column(ForeignKey('data_rest_caching_comp_option.comp_id', ondelete='CASCADE'), primary_key=True,
                     nullable=False)
    payload = Column(LargeBinary)
    updated_at = Column(DateTime(True), server_default=text("now()"))

    comp = relationship('DataRestCachingCompOption')
    filter = relationship('DataRestCachingFilterOption')
    query = relationship('DataRestCachingQueryOption')
    site = relationship('Site')


class Device(Base):
    __tablename__ = 'devices'
    __table_args__ = (
        UniqueConstraint('site_code', 'device_name'),
    )

    device_id = Column(Integer, primary_key=True, server_default=text("nextval('devices_device_id_seq'::regclass)"))
    site_code = Column(ForeignKey('sites.site_code'), nullable=False)
    device_name = Column(String(64), nullable=False)
    equip_type_id = Column(ForeignKey('equipment_types.equip_type_id'))
    creation_time = Column(DateTime(True), server_default=text("now()"))

    equip_type = relationship('EquipmentType')
    site = relationship('Site')


class FaultDiagnosi(Base):
    __tablename__ = 'fault_diagnosis'
    __table_args__ = (
        UniqueConstraint('log_datetime', 'site_code', 'equip_type_id', 'device_name'),
    )

    fault_id = Column(Integer, primary_key=True, server_default=text("nextval('vav_faults_fault_id_seq'::regclass)"))
    log_datetime = Column(TIMESTAMP(True, 0), nullable=False)
    detailed_result = Column(JSONB(astext_type=Text()))
    plot_metadata = Column(JSONB(astext_type=Text()))
    severity = Column(String(16))
    equip_type_id = Column(ForeignKey('equipment_types.equip_type_id'))
    fault_category = Column(JSONB(astext_type=Text()))
    device_name = Column(String)
    site_code = Column(ForeignKey('sites.site_code'))
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    impact = Column(JSONB(astext_type=Text()), server_default=text("'[]'::jsonb"))

    equip_type = relationship('EquipmentType')
    site = relationship('Site')


class FaultFeatureNew(Base):
    __tablename__ = 'fault_feature_new'

    log_datetime = Column(DateTime(True), primary_key=True, nullable=False)
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    feature_type_id = Column(ForeignKey('fault_feature_type_new.feature_type_id'), primary_key=True, nullable=False)
    value_json = Column(JSONB(astext_type=Text()))
    site_code = Column(ForeignKey('sites.site_code'), primary_key=True, nullable=False)
    device_name = Column(String(64), primary_key=True, nullable=False)

    feature_type = relationship('FaultFeatureTypeNew')
    site = relationship('Site')


class FaultSymptom(Base):
    __tablename__ = 'fault_symptom'

    log_datetime = Column(DateTime(True), primary_key=True, nullable=False)
    created_at = Column(DateTime(True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(True))
    symptom_type_id = Column(ForeignKey('fault_symptom_type.symptom_type_id'), primary_key=True, nullable=False)
    detected = Column(Boolean, comment='conflict update')
    value_json = Column(JSONB(astext_type=Text()), comment='conflict update')
    device_name = Column(String, primary_key=True, nullable=False)
    site_code = Column(ForeignKey('sites.site_code'), primary_key=True, nullable=False)

    site = relationship('Site')
    symptom_type = relationship('FaultSymptomType')


t_link_site_func_group = Table(
    'link_site_func_group', metadata,
    Column('site_code', ForeignKey('sites.site_code'), nullable=False),
    Column('func_group_id', ForeignKey('function_group.func_group_id')),
    Column('created_at', DateTime(True)),
    Column('updated_at', DateTime(True)),
    Column('deleted_at', DateTime(True))
)

t_link_user_group = Table(
    'link_user_group', metadata,
    Column('user_id', ForeignKey('users.id', onupdate='CASCADE'), nullable=False),
    Column('group_id', ForeignKey('user_group.id'), nullable=False),
    Column('created_at', DateTime(True)),
    Column('updated_at', DateTime(True)),
    Column('deleted_at', DateTime(True))
)

t_link_user_group_site_func = Table(
    'link_user_group_site_func', metadata,
    Column('user_group_id', ForeignKey('user_group.id', onupdate='CASCADE'), nullable=False),
    Column('func_id', ForeignKey('functions.func_id'), nullable=False),
    Column('created_at', DateTime(True)),
    Column('updated_at', DateTime(True)),
    Column('deleted_at', DateTime(True)),
    Column('site_code', ForeignKey('sites.site_code'), nullable=False),
    Column('func_group_id', ForeignKey('function_group.func_group_id'))
)


class FaultFeature(Base):
    __tablename__ = 'fault_features'

    device_id = Column(ForeignKey('devices.device_id'), primary_key=True, nullable=False)
    feature_type_id = Column(ForeignKey('fault_feature_types.feature_type_id'), primary_key=True, nullable=False)
    log_date = Column(Date, primary_key=True, nullable=False)
    value_json = Column(JSONB(astext_type=Text()))

    device = relationship('Device')
    feature_type = relationship('FaultFeatureType')


class UserDashboard(Base):
    __tablename__ = 'user_dashboard'

    start_from = Column(DateTime(True))
    start_to = Column(DateTime(True))
    ordering = Column(Integer, nullable=False)
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True), index=True)
    version = Column(Integer, nullable=False, server_default=text("0"))
    dashboard_id = Column(ForeignKey('dashboards.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True,
                          nullable=False, index=True)
    user_id = Column(ForeignKey('users.id', onupdate='CASCADE'), primary_key=True, nullable=False, index=True)
    tenant_id = Column(ForeignKey('tenants.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=False, index=True)
    children_list = Column(ARRAY(UUID()))

    dashboard = relationship('Dashboard')
    tenant = relationship('Tenant')
    user = relationship('User')


class WidgetLayout(Base):
    __tablename__ = 'widget_layout'
    __table_args__ = (
        Index('widget_layout_widget_data_id_idx', 'deleted_at', 'widget_data_id'),
        Index('widget_layout_dashboard_id_idx', 'deleted_at', 'dashboard_id')
    )

    dashboard_id = Column(ForeignKey('dashboards.id', ondelete='CASCADE', onupdate='CASCADE'),
                          info={'alias_name': 'primary_key'}, primary_key=True, nullable=False)
    primary_key = synonym('dashboard_id')
    tenant_id = Column(ForeignKey('tenants.id', ondelete='SET NULL', onupdate='CASCADE'), nullable=False)
    widget_data_id = Column(ForeignKey('widget_info.id'), nullable=False)
    user_id = Column(ForeignKey('users.id', onupdate='CASCADE'), nullable=False)
    x = Column(Integer, nullable=False, server_default=text("0"))
    y = Column(Integer, nullable=False, server_default=text("0"))
    h = Column(Integer, nullable=False, server_default=text("0"))
    w = Column(Integer, nullable=False, server_default=text("0"))
    start_from = Column(DateTime(True))
    start_to = Column(DateTime(True))
    created_at = Column(DateTime(True), nullable=False)
    updated_at = Column(DateTime(True), nullable=False)
    deleted_at = Column(DateTime(True))
    version = Column(Integer, nullable=False, server_default=text("0"))

    dashboard = relationship('Dashboard')
    tenant = relationship('Tenant')
    user = relationship('User')
    widget_data = relationship('WidgetInfo')


class UntitledTable256(Base):
    __tablename__ = 'untitled_table_256'
    __table_args__ = (
        UniqueConstraint('id', 'int4_value', 'float4_value'),
    )

    id = Column(Integer, primary_key=True, nullable=False,
                server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False, server_default=text("false"))
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float, nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
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
    uuid_value = Column(UUID)
    varchar_value = Column(String)
    xml_value = Column(NullType)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))
    box_valaue = Column(NullType)

    def test(self):
        print('ok')


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


class Parent(Base):
    __tablename__ = 'test_left'
    id = Column(Integer, primary_key=True)
    children = relationship("Child",
                            secondary=association_table)
    children_second = relationship("ChildSecond",
                                   secondary=association_table_second)


class ChildSecond(Base):
    __tablename__ = 'test_right_second'
    id = Column(Integer, primary_key=True)


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
                                              db_model=Child,
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

[app.include_router(i) for i in
 [crud_route_association_table_second, crud_route_child_second, crud_route_parent, crud_route_child,
  crud_route_association]]

# crud_route_2 = crud_router_builder(db_session=get_transaction_session,
#                                    db_model=UntitledTable256,
#                                    crud_methods=[
#                                        CrudMethods.UPSERT_MANY,
#                                    ],
#                                    exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
#                                    prefix="/friend",
#                                    )
# app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
