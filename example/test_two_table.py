import asyncio
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey, DateTime, Text, text, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from fastapi_quickcrud import CrudMethods
from fastapi_quickcrud import crud_router_builder
from fastapi_quickcrud import sqlalchemy_table_to_pydantic
from fastapi_quickcrud import sqlalchemy_to_pydantic

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

#
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


class UserGroup(Base):
    __tablename__ = 'user_group'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    tenant_id = Column(ForeignKey('tenants.id', onupdate='CASCADE'), nullable=False)
    group_name = Column(String, nullable=False)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    deleted_at = Column(DateTime(True))
    description = Column(Text)
    policy_id = Column(UUID(as_uuid=True))
    icon_url = Column(Text)

    tenant = relationship('Tenant')

# friend = Table(
#     'friend', metadata,
#     Column('id', ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
#     Column('friend_name', String, nullable=False)
# )
# class User(Base):
#     __tablename__ = 'users'
#
#     id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
#     name = Column(ForeignKey('users.id', onupdate='CASCADE'),nullable=False)
#     email = Column(String, nullable=False, default=datetime.now(timezone.utc).strftime('%H:%M:%S%z'))
#     friend = relationship('friend')
# async def test():
#     stmt = select(*[UserGroup, Tenant]).join(*[Tenant]).where(1==1)
#     async with async_session() as session:
#         async with session.begin():
#             result = await session.execute(stmt)
#     for i in result:
#         print(dir(i))
# asyncio.run(test())
user_model_set = sqlalchemy_to_pydantic(db_model=UserGroup,
                                        crud_methods=[
                                            CrudMethods.FIND_MANY,
                                            CrudMethods.FIND_ONE,
                                            CrudMethods.UPSERT_ONE,
                                            CrudMethods.UPDATE_MANY,
                                            CrudMethods.UPDATE_ONE,
                                            CrudMethods.DELETE_ONE,
                                            CrudMethods.DELETE_MANY,
                                            CrudMethods.PATCH_MANY,

                                        ],
                                        exclude_columns=[])

friend_model_set = sqlalchemy_to_pydantic(db_model=Tenant,
                                                crud_methods=[
                                                    CrudMethods.FIND_MANY,
                                                    CrudMethods.UPSERT_MANY,
                                                    CrudMethods.UPDATE_MANY,
                                                    CrudMethods.DELETE_MANY,
                                                    CrudMethods.PATCH_MANY,

                                                ],
                                                exclude_columns=[])


crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=user_model_set,
                                   db_model=UserGroup,
                                   prefix="/user",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["User"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=friend_model_set,
                                   db_model=Tenant,
                                   async_mode=True,
                                   prefix="/friend",
                                   dependencies=[],
                                   tags=["Friend"]
                                   )


app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
