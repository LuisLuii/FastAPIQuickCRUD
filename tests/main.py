import uuid

import uvicorn
from fastapi import FastAPI
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
class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class UntitledTable256(Base):
    __tablename__ = 'untitled_table_256'
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
    xml_value = Column(NullType)
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))
    box_valaue = Column(NullType)



t_test_foregine = Table(
    'test_foregine', metadata,
    Column('customer_id', ForeignKey('sites.site_code')),
    Column('contact_name', String(255), nullable=False),
    Column('phone', String(15)),
    Column('email', String(100))
)



UntitledTable256_service = CrudService(model=UntitledTable256)

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
a = UntitledTable256Model.__dict__

test_create_one = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_creation_one",
                          tags=["test"]
                          )
UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_MANY,
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_many = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_creation_many",
                          tags=["test"]
                          )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudRouter.FIND_ONE,
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_one = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_creation_one",
                          tags=["test"]
                          )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_MANY
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test2 = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_end_point_2",
                          tags=["test"]
                          )
UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudRouter.POST_REDIRECT_GET
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test3 = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_end_point_3",
                          tags=["test"]
                          )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
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
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_get_data = crud_router(db_session=get_transaction_session,
                          crud_service=UntitledTable256_service,
                          crud_models=UntitledTable256Model,
                          prefix="/test_CRUD",
                          tags=["test"]
                          )





# test_table_service = CrudService(model=t_test_foregine)
#
# UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
#                                                crud_methods=[
#                                                    CrudRouter.UPSERT_ONE
#                                                ],
#                                                exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
#
# test_create_one = crud_router(db_session=get_transaction_session,
#                           crud_service=test_table_service,
#                           crud_models=UntitledTable256Model,
#                           prefix="/test_creation_one",
#                           tags=["test"]
#                           )
class test_777(Base):
    __tablename__ = 'test_build_myself'
    __table_args__ = (
        UniqueConstraint('id','float4_value', 'int4_value'),
    )

    id = Column(Integer, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
    bool_value = Column(Boolean, nullable=False)
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date, server_default=text("now()"))
    float4_value = Column(Float, nullable=False)
    float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
    int8_value = Column(BigInteger, default=99)
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
    array_value = Column(ARRAY(Integer()))
    array_str__value = Column(ARRAY(String()))

# test_777.__table__.create(engine)
[app.include_router(i) for i in [test_get_data,test3,test2]]
uvicorn.run(app, host="0.0.0.0", port=8001, debug=False)
