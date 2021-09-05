import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from fastapi_quickcrud import crud_router_builder

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata


engine = create_async_engine('postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres', future=True, echo=True,
                             pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
async_session = sessionmaker(bind=engine, class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        async with session.begin():
            yield session



Base = declarative_base()
metadata = Base.metadata


class Parent(Base):
    __tablename__ = 'parent_o2o'
    id = Column(Integer, primary_key=True)

    # one-to-many collection
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = 'child_o2o'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent_o2o.id'))

    # many-to-one scalar
    parent = relationship("Parent", back_populates="children")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                   db_model=Parent,
                                   prefix="/Parent",
                                   tags=['parent']
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   db_model=Child,
                                   prefix="/Child",
                                   tags=['child']
                                   )

app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
