import asyncio
import inspect
from functools import partial
from typing import \
    Any, \
    List, \
    TypeVar, Union, Callable, Optional

from fastapi import \
    Depends, APIRouter
from pydantic import \
    BaseModel
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql.schema import Table

from . import sqlalchemy_to_pydantic
from .misc.abstract_execute import SQLALchemyExecuteService
from .misc.abstract_parser import SQLAlchemyGeneralSQLeResultParse
from .misc.abstract_query import SQLAlchemyPGSQLQueryService, \
    SQLAlchemySQLITEQueryService, SQLAlchemyNotSupportQueryService
from .misc.abstract_route import SQLAlchemySQLLiteRouteSource, SQLAlchemyPGSQLRouteSource, \
    SQLAlchemyNotSupportRouteSource
from .misc.crud_model import CRUDModel
from .misc.memory_sql import async_memory_db, sync_memory_db
from .misc.type import CrudMethods, SqlType

CRUDModelType = TypeVar("CRUDModelType", bound=BaseModel)
CompulsoryQueryModelType = TypeVar("CompulsoryQueryModelType", bound=BaseModel)
OnConflictModelType = TypeVar("OnConflictModelType", bound=BaseModel)


def crud_router_builder(
        *,
        db_model: Union[Table, 'DeclarativeBaseModel'],
        db_session: Callable = None,
        autocommit: bool = True,
        crud_methods: Optional[List[CrudMethods]] = None,
        exclude_columns: Optional[List[str]] = None,
        dependencies: Optional[List[callable]] = None,
        crud_models: Optional[CRUDModel] = None,
        async_mode: Optional[bool] = None,
        **router_kwargs: Any) -> APIRouter:
    """
    :param db_session: Callable function
        db_session should be a callable function, and return a session generator.
        Also you can handle commit by yourelf or othe business logic

        SQLAlchemy based example(SQLAlchemy was supported async since 1.4 version):
            async:
            async def get_transaction_session() -> AsyncSession:
                async with async_session() as session:
                    async with session.begin():
                        yield session
            sync:
            def get_transaction_session():
                try:
                    db = sync_session()
                    yield db
                    db.commit()
                except Exception as e:
                    db.rollback()
                    raise e
                finally:
                    db.close()


    :param crud_methods: List[CrudMethods]
        Fastapi Quick CRUD supports a few of crud methods, and they save into the Enum class,
        get it by : from fastapi_quickcrud import CrudMethods
        example:
            [CrudMethods.GET_MANY,CrudMethods.ONE]
        note:
            if there is no primary key in your SQLAlchemy model, it dose not support request with
            specific resource, such as GET_ONE, UPDATE_ONE, DELETE_ONE, PATCH_ONE AND POST_REDIRECT_GET
            this is because POST_REDIRECT_GET need to redirect to GET_ONE api

    :param exclude_columns: List[str]
        Fastapi Quick CRUD will get all the columns in you table to generate a CRUD router,
        it is allow you exclude some columns you dont want it expose to operated by API
        note:
            if the column in exclude list but is it not nullable or no default_value, it may throw error
            when you do insert

    :param crud_models:
    :param db_model:
        SQLAlchemy model,
    :param dependencies:
    :param async_mode:
    :param autocommit:
    :param router_kwargs:  Optional arguments that ``APIRouter().include_router`` takes.
    :return:
    """
    NO_PRIMARY_KEY = False

    if isinstance(db_model, Table):
        db_name = str(db_model.fullname)
        table_dict = {'__table__': db_model,
                      '__tablename__': db_name}

        if not db_model.primary_key:
            table_dict['__mapper_args__'] = {
                "primary_key": [i for i in db_model._columns]
            }
            NO_PRIMARY_KEY = True

        for i in db_model.c:
            col, = i.expression.base_columns
            table_dict[str(i.key)] = col

        tmp = type(f'{db_name}DeclarativeBaseClass', (declarative_base(),), table_dict)
        db_model = tmp

    constraints = db_model.__table__.constraints

    if db_session is None:
        if async_mode:
            db_connection = async_memory_db
            db_session: Callable = db_connection.async_get_memory_db_session
        else:
            db_connection = sync_memory_db
            db_session: Callable = db_connection.get_memory_db_session
        db_connection.create_memory_table(db_model)

    if async_mode is None:
        async_mode = inspect.isasyncgen(db_session())
    if async_mode:
        async def async_runner(f):
            return [i.bind.name async for i in f()]

        sql_type, = asyncio.get_event_loop().run_until_complete(async_runner(db_session))
    else:
        sql_type, = [i.bind.name for i in db_session()]

    if not crud_methods and NO_PRIMARY_KEY == False:
        crud_methods = CrudMethods.get_declarative_model_full_crud_method()
    if not crud_methods and NO_PRIMARY_KEY == True:
        crud_methods = CrudMethods.get_table_full_crud_method()
    result_parser_builder = SQLAlchemyGeneralSQLeResultParse

    if sql_type == SqlType.sqlite:
        routes_source = SQLAlchemySQLLiteRouteSource
        query_service = SQLAlchemySQLITEQueryService
    elif sql_type == SqlType.postgresql:
        routes_source = SQLAlchemyPGSQLRouteSource
        query_service = SQLAlchemyPGSQLQueryService
    else:
        routes_source = SQLAlchemyNotSupportRouteSource
        query_service = SQLAlchemyNotSupportQueryService

    if not crud_models:
        crud_models_builder: CRUDModel = sqlalchemy_to_pydantic
        crud_models: CRUDModel = crud_models_builder(db_model=db_model,
                                                     constraints=constraints,
                                                     crud_methods=crud_methods,
                                                     exclude_columns=exclude_columns,
                                                     sql_type=sql_type,
                                                     exclude_primary_key=NO_PRIMARY_KEY)

    crud_service = query_service(model=db_model, async_mode=async_mode)
    # else:
    #     crud_service = SQLAlchemyPostgreQueryService(model=db_model, async_mode=async_mode)

    result_parser = result_parser_builder(async_model=async_mode,
                                          crud_models=crud_models,
                                          autocommit=autocommit)
    methods_dependencies = crud_models.get_available_request_method()
    primary_name = crud_models.PRIMARY_KEY_NAME
    if primary_name:
        path = '/{' + primary_name + '}'
    else:
        path = ""
    unique_list: List[str] = crud_models.UNIQUE_LIST

    execute_service = SQLALchemyExecuteService()

    def find_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)
        routes_source.find_one(path=path,
                               request_url_param_model=_request_url_param_model,
                               request_query_model=_request_query_model,
                               response_model=_response_model,
                               db_session=db_session,
                               query_service=crud_service,
                               parsing_service=result_parser,
                               execute_service=execute_service,
                               dependencies=dependencies,
                               api=api,
                               async_mode=async_mode)

    def find_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        routes_source.find_many(path="",
                                request_query_model=_request_query_model,
                                response_model=_response_model,
                                db_session=db_session,
                                query_service=crud_service,
                                parsing_service=result_parser,
                                execute_service=execute_service,
                                dependencies=dependencies,
                                api=api,
                                async_mode=async_mode)

    def upsert_one_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)
        routes_source.upsert_one(path="",
                                 request_body_model=_request_body_model,
                                 response_model=_response_model,
                                 db_session=db_session,
                                 query_service=crud_service,
                                 parsing_service=result_parser,
                                 execute_service=execute_service,
                                 dependencies=dependencies,
                                 api=api,
                                 async_mode=async_mode,
                                 unique_list=unique_list)

    def upsert_many_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        routes_source.upsert_many(path="",
                                  request_body_model=_request_body_model,
                                  response_model=_response_model,
                                  db_session=db_session,
                                  query_service=crud_service,
                                  parsing_service=result_parser,
                                  execute_service=execute_service,
                                  dependencies=dependencies,
                                  api=api,
                                  unique_list=unique_list,
                                  async_mode=async_mode)

    def create_one_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)
        routes_source.create_one(path="",
                                 request_body_model=_request_body_model,
                                 response_model=_response_model,
                                 db_session=db_session,
                                 query_service=crud_service,
                                 parsing_service=result_parser,
                                 execute_service=execute_service,
                                 dependencies=dependencies,
                                 api=api,
                                 async_mode=async_mode,
                                 unique_list=unique_list)

    def create_many_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        routes_source.create_many(path="",
                                  request_body_model=_request_body_model,
                                  response_model=_response_model,
                                  db_session=db_session,
                                  query_service=crud_service,
                                  parsing_service=result_parser,
                                  execute_service=execute_service,
                                  dependencies=dependencies,
                                  api=api,
                                  unique_list=unique_list,
                                  async_mode=async_mode)

    def delete_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _request_url_model = request_response_model.get('requestUrlParamModel', None)
        _response_model = request_response_model.get('responseModel', None)

        routes_source.delete_one(path=path,
                                 request_query_model=_request_query_model,
                                 request_url_model=_request_url_model,
                                 response_model=_response_model,
                                 db_session=db_session,
                                 query_service=crud_service,
                                 parsing_service=result_parser,
                                 execute_service=execute_service,
                                 dependencies=dependencies,
                                 api=api,
                                 async_mode=async_mode)

    def delete_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)

        routes_source.delete_many(path="",
                                  request_query_model=_request_query_model,
                                  response_model=_response_model,
                                  db_session=db_session,
                                  query_service=crud_service,
                                  parsing_service=result_parser,
                                  execute_service=execute_service,
                                  dependencies=dependencies,
                                  api=api,
                                  async_mode=async_mode)

    def post_redirect_get_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        routes_source.post_redirect_get(api=api,
                                        dependencies=dependencies,
                                        request_body_model=_request_body_model,
                                        db_session=db_session,
                                        crud_service=crud_service,
                                        result_parser=result_parser,
                                        execute_service=execute_service,
                                        async_mode=async_mode,
                                        response_model=_response_model)

    def patch_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        routes_source.patch_one(api=api,
                                path=path,
                                request_url_param_model=_request_url_param_model,
                                request_query_model=_request_query_model,
                                dependencies=dependencies,
                                request_body_model=_request_body_model,
                                db_session=db_session,
                                crud_service=crud_service,
                                result_parser=result_parser,
                                execute_service=execute_service,
                                async_mode=async_mode,
                                response_model=_response_model)

    def patch_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)

        routes_source.patch_many(api=api,
                                 path="",
                                 request_query_model=_request_query_model,
                                 dependencies=dependencies,
                                 request_body_model=_request_body_model,
                                 db_session=db_session,
                                 crud_service=crud_service,
                                 result_parser=result_parser,
                                 execute_service=execute_service,
                                 async_mode=async_mode,
                                 response_model=_response_model)

    def put_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)
        routes_source.put_one(api=api,
                              path=path,
                              request_query_model=_request_query_model,
                              dependencies=dependencies,
                              request_body_model=_request_body_model,
                              db_session=db_session,
                              crud_service=crud_service,
                              result_parser=result_parser,
                              execute_service=execute_service,
                              async_mode=async_mode,
                              response_model=_response_model,
                              request_url_param_model=_request_url_param_model)

    def put_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)

        routes_source.put_many(api=api,
                               path='',
                               request_query_model=_request_query_model,
                               dependencies=dependencies,
                               request_body_model=_request_body_model,
                               db_session=db_session,
                               crud_service=crud_service,
                               result_parser=result_parser,
                               execute_service=execute_service,
                               async_mode=async_mode,
                               response_model=_response_model)

    api_register = {
        CrudMethods.FIND_ONE.value: find_one_api,
        CrudMethods.FIND_MANY.value: find_many_api,
        CrudMethods.UPSERT_ONE.value: upsert_one_api,
        CrudMethods.UPSERT_MANY.value: upsert_many_api,
        CrudMethods.CREATE_MANY.value: create_many_api,
        CrudMethods.CREATE_ONE.value: create_one_api,
        CrudMethods.DELETE_ONE.value: delete_one_api,
        CrudMethods.DELETE_MANY.value: delete_many_api,
        CrudMethods.POST_REDIRECT_GET.value: post_redirect_get_api,
        CrudMethods.PATCH_ONE.value: patch_one_api,
        CrudMethods.PATCH_MANY.value: patch_many_api,
        CrudMethods.UPDATE_ONE.value: put_one_api,
        CrudMethods.UPDATE_MANY.value: put_many_api
    }
    api = APIRouter(**router_kwargs)

    if dependencies is None:
        dependencies = []
    dependencies = [Depends(dep) for dep in dependencies]
    for request_method in methods_dependencies:
        value_of_dict_crud_model = crud_models.get_model_by_request_method(request_method)
        crud_model_of_this_request_methods = value_of_dict_crud_model.keys()
        for crud_model_of_this_request_method in crud_model_of_this_request_methods:
            request_response_model_of_this_request_method = value_of_dict_crud_model[crud_model_of_this_request_method]
            api_register[crud_model_of_this_request_method.value](request_response_model_of_this_request_method,
                                                                  dependencies)

    return api


pgsql_crud_router_builder = partial(crud_router_builder, sql_type='postgresql')
generic_sql_crud_router_builder = partial(crud_router_builder, sql_type='')
