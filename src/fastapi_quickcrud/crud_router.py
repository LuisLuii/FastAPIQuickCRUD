from typing import \
    Any, \
    List, \
    TypeVar

from fastapi import \
    APIRouter, \
    Depends
from pydantic import \
    BaseModel
from sqlalchemy.sql.schema import Table

from .misc.abstract_execute import SQLALchemyExecuteService
from .misc.abstract_parser import SQLAlchemyResultParse, SQLAlchemyTableResultParse
from .misc.abstract_query import SQLAlchemyQueryService
from .misc.abstract_route import SQLALChemyBaseRouteSource
from .misc.crud_model import CRUDModel
from .misc.type import CrudMethods

CRUDModelType = TypeVar("CRUDModelType", bound=BaseModel)
CompulsoryQueryModelType = TypeVar("CompulsoryQueryModelType", bound=BaseModel)
OnConflictModelType = TypeVar("OnConflictModelType", bound=BaseModel)


def crud_router_builder(
        *,
        db_session,
        crud_models: CRUDModel,
        db_model,
        dependencies: List[callable] = None,
        async_mode=False,
        autocommit=True,
        **router_kwargs: Any) -> APIRouter:
    """
    :param db_session: db_session
    :param crud_models:
    :param db_model:
    :param dependencies:
    :param async_mode:
    :param autocommit:
    :param router_kwargs:  Optional arguments that ``APIRouter().include_router`` takes.
    :return:
    """

    if dependencies is None:
        dependencies = []
    api = APIRouter(**router_kwargs)
    methods_dependencies = crud_models.get_available_request_method()
    primary_name = crud_models.PRIMARY_KEY_NAME
    if primary_name:
        path = '/{' + primary_name + '}'
    else:
        path = ""
    unique_list: List[str] = crud_models.UNIQUE_LIST
    dependencies = [Depends(dep) for dep in dependencies]

    routes_source = SQLALChemyBaseRouteSource

    if isinstance(db_model, Table):
        result_parser = SQLAlchemyTableResultParse(async_model=async_mode,
                                                   crud_models=crud_models,
                                                   autocommit=autocommit)
    else:
        result_parser = SQLAlchemyResultParse(async_model=async_mode,
                                              crud_models=crud_models,
                                              autocommit=autocommit)
    crud_service = SQLAlchemyQueryService(model=db_model, async_mode=async_mode)

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
        CrudMethods.DELETE_ONE.value: delete_one_api,
        CrudMethods.DELETE_MANY.value: delete_many_api,
        CrudMethods.POST_REDIRECT_GET.value: post_redirect_get_api,
        CrudMethods.PATCH_ONE.value: patch_one_api,
        CrudMethods.PATCH_MANY.value: patch_many_api,
        CrudMethods.UPDATE_ONE.value: put_one_api,
        CrudMethods.UPDATE_MANY.value: put_many_api
    }
    for request_method in methods_dependencies:
        value_of_dict_crud_model = crud_models.get_model_by_request_method(request_method)
        crud_model_of_this_request_methods = value_of_dict_crud_model.keys()
        for crud_model_of_this_request_method in crud_model_of_this_request_methods:
            request_response_model_of_this_request_method = value_of_dict_crud_model[crud_model_of_this_request_method]
            api_register[crud_model_of_this_request_method.value](request_response_model_of_this_request_method,
                                                                  dependencies)

    return api
