import uvicorn
from fastapi import FastAPI
from src.fastapi_quickcrud import CrudMethods
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_table_to_pydantic
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from sqlalchemy import Column, Integer, \
    String, text, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

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


class RelationshipTestA(Base):
    __tablename__ = 'relationship_test_a'

    id = Column(Integer, primary_key=True, server_default=text("nextval('untitled_table_271_id_seq'::regclass)"))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


t_relationship_test_b = Table(
    'relationship_test_b', metadata,
    Column('id', ForeignKey('relationship_test_a.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend', String, nullable=False)
)

RelationshipTestA_pydantic_set = sqlalchemy_to_pydantic(db_model=RelationshipTestA,
                                                        crud_methods=[
                                                            CrudMethods.FIND_MANY,
                                                            CrudMethods.FIND_ONE,
                                                            CrudMethods.UPSERT_MANY,
                                                            CrudMethods.UPDATE_MANY,
                                                            CrudMethods.UPDATE_ONE,
                                                            CrudMethods.DELETE_ONE,
                                                            CrudMethods.DELETE_MANY,
                                                            CrudMethods.PATCH_MANY,

                                                        ],
                                                        exclude_columns=[])

RelationshipTestB_pydantic_set = sqlalchemy_table_to_pydantic(db_model=t_relationship_test_b,
                                                              crud_methods=[
                                                                  CrudMethods.FIND_MANY,
                                                                  CrudMethods.UPSERT_MANY,
                                                                  CrudMethods.UPDATE_MANY,
                                                                  CrudMethods.DELETE_MANY,
                                                                  CrudMethods.PATCH_MANY,

                                                              ],
                                                              exclude_columns=[])
crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=RelationshipTestA_pydantic_set,
                                   db_model=t_relationship_test_b,
                                   prefix="/crud_test_a",
                                   dependencies=[],
                                   tags=["A"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=RelationshipTestB_pydantic_set,
                                   db_model=t_relationship_test_b,
                                   prefix="/crud_test",
                                   dependencies=[],
                                   tags=["B"]
                                   )

app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
