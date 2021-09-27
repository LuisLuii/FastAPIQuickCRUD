import uvicorn
from fastapi import FastAPI
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym
from sqlalchemy.testing.schema import Table

from fastapi_quickcrud.misc.utils import sqlalchemy_table_to_pydantic
from src.fastapi_quickcrud import CrudMethods as CrudRouter
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_to_pydantic

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


ExampleTable = Table(
    'untitled_table_256', metadata,
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
    Column('text_value', Text),
    Column('time_value', Time),
    Column('timestamp_value', DateTime),
    Column('timestamptz_value', DateTime(True)),
    Column('timetz_value', Time(True)),
    Column('uuid_value', UUID),
    Column('varchar_value', String),
    Column('array_value', ARRAY(Integer())),
    Column('array_str__value', ARRAY(String())),
    UniqueConstraint( 'int4_value', 'float4_value'),
)


UntitledTable256Model = sqlalchemy_table_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

UntitledTable256Model = sqlalchemy_table_to_pydantic(ExampleTable,
                                               crud_methods=[
                                                   CrudRouter.UPSERT_MANY
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

upsert_many_router = crud_router_builder(db_session=get_transaction_session,
                                         db_model=ExampleTable,
                                         crud_models=UntitledTable256Model,
                                         prefix="/create_many",
                                         async_mode=True,
                                         tags=["test"]
                                         )

example_table_full_api = sqlalchemy_table_to_pydantic(ExampleTable,
                                                crud_methods=[
                                                    CrudRouter.FIND_MANY,
                                                    CrudRouter.UPSERT_ONE,
                                                    CrudRouter.UPDATE_MANY,
                                                    CrudRouter.DELETE_MANY,
                                                    CrudRouter.PATCH_MANY,

                                                ],
                                                exclude_columns=['array_str__value', 'bytea_value', 'xml_value',
                                                                 'box_valaue'])

example_table_full_router = crud_router_builder(db_session=get_transaction_session,
                                                db_model=ExampleTable,
                                                crud_models=example_table_full_api,
                                                async_mode=True,
                                                prefix="/test_CRUD",
                                                tags=["test"]
                                                )
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
[app.include_router(i) for i in [example_table_full_router, upsert_many_router]]
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
