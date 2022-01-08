import asyncio
import os

from fastapi import FastAPI
from sqlalchemy import ARRAY, BigInteger, Boolean, CHAR, Column, Date, DateTime, Float, Integer, \
    JSON, LargeBinary, Numeric, SmallInteger, String, Text, Time, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import declarative_base, sessionmaker, synonym

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_ASYNC_URL',
                                   'postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres')
app = FastAPI()

Base = declarative_base()
metadata = Base.metadata
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_ASYNC_URL',
                                   'postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres')

engine = create_async_engine(TEST_DATABASE_URL,
                             future=True,
                             echo=True,
                             pool_use_lifo=True,
                             pool_pre_ping=True,
                             pool_recycle=7200)
async_session = sessionmaker(autocommit=False,
                             autoflush=False,
                             bind=engine,
                             class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        yield session


class UntitledTable256(Base):
    primary_key_of_table = "primary_key"
    unique_fields = ['primary_key', 'int4_value', 'float4_value']
    __tablename__ = 'test_build_myself_async'
    __table_args__ = (
        UniqueConstraint('primary_key', 'int4_value', 'float4_value'),
    )
    primary_key = Column(Integer, primary_key=True, info={'alias_name': 'primary_key'},autoincrement=True)
    bool_value = Column(Boolean, nullable=False)
    bytea_value = Column(LargeBinary)
    char_value = Column(CHAR(10))
    date_value = Column(Date)
    float4_value = Column(Float, nullable=False)
    float8_value = Column(Float(53), nullable=False)
    int2_value = Column(SmallInteger, nullable=False)
    int4_value = Column(Integer, nullable=False)
    int8_value = Column(BigInteger)
    numeric_value = Column(Numeric)
    text_value = Column(Text)
    time_value = Column(Time)
    timestamp_value = Column(DateTime)
    timestamptz_value = Column(DateTime(True))
    timetz_value = Column(Time(True))
    varchar_value = Column(String)
    # xml_value = Column(NullType)
    # box_valaue = Column(NullType)


async def create_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# loop = asyncio.get_event_loop()
# loop.run_until_complete(create_table())
# loop.close()
