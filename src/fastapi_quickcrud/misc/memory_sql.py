import asyncio
import string
import random
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


class MemorySql():
    def __init__(self, async_mode=False):
        self.async_mode = async_mode
        sqlite_shared_name = "test_db_{}".format(
            'fastapi_quick_crud'
            # ''.join(random.sample(string.ascii_letters, k=4))
        )
        a = ''.join(random.sample(string.ascii_letters, k=4))
        SQLALCHEMY_DATABASE_URL = f"sqlite{'+aiosqlite' if async_mode else ''}:///file:{sqlite_shared_name}?mode=memory&cache=shared&uri=true"
        print(SQLALCHEMY_DATABASE_URL)
        if not async_mode:
            self.engine = create_engine(SQLALCHEMY_DATABASE_URL,
                                        future=True,
                                        echo=True,
                                        pool_pre_ping=True,
                                        pool_recycle=7200,
                                        connect_args={"check_same_thread": False},
                                        poolclass=StaticPool)
            self.sync_session = sessionmaker(bind=self.engine,
                                             autocommit=False, )
        else:

            self.engine = create_async_engine(SQLALCHEMY_DATABASE_URL,
                                              future=True,
                                              echo=True,
                                              pool_pre_ping=True,
                                              pool_recycle=7200,
                                              connect_args={"check_same_thread": False},
                                              poolclass=StaticPool)
            self.sync_session = sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=self.engine,
                                             class_=AsyncSession)

    def create_memory_table(self, Mode: 'declarative_base()'):
        if not self.async_mode:
            Mode.__table__.create(self.engine, checkfirst=True)
        else:
            async def create_table(engine, model):
                async with engine.begin() as conn:
                    await conn.run_sync(model._sa_registry.metadata.create_all)

            loop = asyncio.get_event_loop()
            loop.run_until_complete(create_table(self.engine, Mode))

    def get_memory_db_session(self) -> Generator:
        try:
            db = self.sync_session()
            yield db
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    async def async_get_memory_db_session(self):
        async with self.sync_session() as session:
            yield session

async_memory_db = MemorySql(True)
sync_memory_db = MemorySql()