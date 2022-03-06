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
from .misc.utils import convert_table_to_model, Base

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
        foreign_include: Optional[Base] = None,
        sql_type: Optional[SqlType] = None,
        **router_kwargs: Any) -> APIRouter:
    """
    @param db_model:
        The Sqlalchemy Base model/Table you want to use it to build api.

    @param db_session:
        The callable variable and return a session generator that will be used to get database connection session for fastapi.

    @param autocommit:
        set False if you handle commit in your db_session.

    @param crud_methods:
        Fastapi Quick CRUD supports a few of crud methods, and they save into the Enum class,
        get it by : from fastapi_quickcrud import CrudMethods
        example:
            [CrudMethods.GET_MANY,CrudMethods.ONE]
        note:
            if there is no primary key in your SQLAlchemy model, it dose not support request with
            specific resource, such as GET_ONE, UPDATE_ONE, DELETE_ONE, PATCH_ONE AND POST_REDIRECT_GET
            this is because POST_REDIRECT_GET need to redirect to GET_ONE api

    @param exclude_columns:
        Fastapi Quick CRUD will get all the columns in you table to generate a CRUD router,
        it is allow you exclude some columns you dont want it expose to operated by API
        note:
            if the column in exclude list but is it not nullable or no default_value, it may throw error
            when you do insert

    @param dependencies:
        A variable that will be added to the path operation decorators.

    @param crud_models:
        You can use the sqlalchemy_to_pydantic() to build your own Pydantic model CRUD set

    @param async_mode:
        As your database connection

    @param foreign_include: BaseModel
        Used to build foreign tree api

    @param sql_type:
        You sql database type

    @param router_kwargs:
        other argument for FastApi's views

    @return:
        APIRouter for fastapi
    """

    db_model, NO_PRIMARY_KEY = convert_table_to_model(db_model)

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

    if sql_type is None:
        async def async_runner(f):
            return [i.bind.name async for i in f()]

        try:
            if async_mode:
                sql_type, = asyncio.get_event_loop().run_until_complete(async_runner(db_session))
            else:
                sql_type, = [i.bind.name for i in db_session()]
        except Exception:
            raise RuntimeError("Some unknown problem occurred error, maybe you are uvicorn.run with reload=True. "
                               "Try declaring sql_type for crud_router_builder yourself using from fastapi_quickcrud.misc.type import SqlType")

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
                                                     foreign_include=foreign_include,
                                                     exclude_primary_key=NO_PRIMARY_KEY)

    foreign_table_mapping = {db_model.__tablename__: db_model}
    if foreign_include:
        for i in foreign_include:
            model , _= convert_table_to_model(i)
            foreign_table_mapping[model.__tablename__] = i
    crud_service = query_service(model=db_model, async_mode=async_mode, foreign_table_mapping=foreign_table_mapping)
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

    def find_one_foreign_tree_api(request_response_model: dict, dependencies):
        _foreign_list_model = request_response_model.get('foreignListModel', None)
        for i in _foreign_list_model:
            _request_query_model = i["request_query_model"]
            _response_model = i["response_model"]
            _path = i["path"]
            _function_name = i["function_name"]
            request_url_param_model = i["primary_key_dataclass_model"]
            routes_source.find_one_foreign_tree(path=_path,
                                                request_query_model=_request_query_model,
                                                response_model=_response_model,
                                                request_url_param_model=request_url_param_model,
                                                db_session=db_session,
                                                query_service=crud_service,
                                                parsing_service=result_parser,
                                                execute_service=execute_service,
                                                dependencies=dependencies,
                                                api=api,
                                                function_name=_function_name,
                                                async_mode=async_mode)

    def find_many_foreign_tree_api(request_response_model: dict, dependencies):
        _foreign_list_model = request_response_model.get('foreignListModel', None)
        for i in _foreign_list_model:
            _request_query_model = i["request_query_model"]
            _response_model = i["response_model"]
            _path = i["path"]
            _function_name = i["function_name"]
            request_url_param_model = i["primary_key_dataclass_model"]
            routes_source.find_many_foreign_tree(path=_path,
                                                 request_query_model=_request_query_model,
                                                 response_model=_response_model,
                                                 request_url_param_model=request_url_param_model,
                                                 db_session=db_session,
                                                 query_service=crud_service,
                                                 parsing_service=result_parser,
                                                 execute_service=execute_service,
                                                 dependencies=dependencies,
                                                 api=api,
                                                 async_mode=async_mode,
                                                 function_name=_function_name)

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
        CrudMethods.UPDATE_MANY.value: put_many_api,
        CrudMethods.FIND_ONE_WITH_FOREIGN_TREE.value: find_one_foreign_tree_api,
        CrudMethods.FIND_MANY_WITH_FOREIGN_TREE.value: find_many_foreign_tree_api
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


pgsql_crud_router_builder = partial(crud_router_builder)
generic_sql_crud_router_builder = partial(crud_router_builder)
