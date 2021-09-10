from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import StaticPool


class MemorySql():
    def __init__(self):

        SQLALCHEMY_DATABASE_URL = "sqlite://"

        self.engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True, echo=True, pool_pre_ping=True, pool_recycle=7200,
                               connect_args={"check_same_thread": False},poolclass=StaticPool)
        self.sync_session = sessionmaker(bind=self.engine)

    def create_memory_table(self, Mode: 'declarative_base()'):
        Mode.__table__.create(self.engine, checkfirst=True)

    def get_memory_db_session(self) -> Generator:
        try:
            db = self.sync_session()
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()



memory_sql_connection = MemorySql()