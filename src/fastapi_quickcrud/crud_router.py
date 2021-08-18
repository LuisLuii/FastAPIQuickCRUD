from http import HTTPStatus
from typing import \
    Any, \
    List, \
    TypeVar, \
    Union

from fastapi import \
    APIRouter, \
    Depends, \
    Response
from pydantic import \
    BaseModel
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from .crud_service import CrudService
from .misc.abstract_parser import SQLALchemyResultParse
from .misc.crud_model import CRUDModel
from .misc.type import CrudMethods

CRUDModelType = TypeVar("CRUDModelType", bound=BaseModel)
CompulsoryQueryModelType = TypeVar("CompulsoryQueryModelType", bound=BaseModel)
OnConflictModelType = TypeVar("OnConflictModelType", bound=BaseModel)


def crud_router_builder(
        *,
        db_session,
        crud_service: CrudService,
        crud_models: CRUDModel,
        dependencies: List[callable] = None,
        async_mode=False,
        autocommit=True,
        **router_kwargs: Any) -> APIRouter:
    """

    :param db_session: db_session
    :param crud_service:
    :param crud_models:
    :param dependencies:
    :param async_mode:
    :param autocommit:
    :param router_kwargs:  Optional arguments that ``APIRouter().include_router`` takes.
    :return:
    """
    if dependencies is None:
        dependencies = []
    api = APIRouter()
    # crud_service = CrudService(model=db_model)
    methods_dependencies = crud_models.get_available_request_method()
    primary_name = crud_models.PRIMARY_KEY_NAME

    path = '/{' + primary_name + '}'
    unique_list: List[str] = crud_models.UNIQUE_LIST

    dependencies = [Depends(dep) for dep in dependencies]
    result_parser = SQLALchemyResultParse(async_model=async_mode,
                                          crud_models=crud_models,
                                          autocommit=autocommit)
    router = APIRouter()

    def find_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.get(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        async def get_one_by_primary_key(response: Response,
                                         url_param: _request_url_param_model = Depends(),
                                         query=Depends(_request_query_model),
                                         session=Depends(db_session)):
            stmt = crud_service.get_one(filter_args=query.__dict__,
                                        extra_args=url_param.__dict__)
            _ = session.execute(stmt)
            query_result = await _ if async_mode else _
            return await result_parser.find_one(response_model=_response_model,
                                                sql_execute_result=query_result,
                                                fastapi_response=response,
                                                session=session)

    def find_many_api(request_response_model: dict, dependencies):

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.get("", response_model=_response_model, dependencies=dependencies)
        async def get_many(response: Response,
                           query=Depends(_request_query_model),
                           session=Depends(
                               db_session)
                           ):
            query_dict = query.__dict__
            limit = query_dict.pop('limit', None)
            offset = query_dict.pop('offset', None)
            order_by_columns = query_dict.pop('order_by_columns', None)
            stmt = crud_service.get_many(
                filter_args=query_dict,
                limit=limit,
                offset=offset, order_by_columns=order_by_columns,
                session=session)
            query_result = session.execute(stmt)
            query_result = await query_result if async_mode else query_result
            return await result_parser.find_many(response_model=_response_model,
                                                 sql_execute_result=query_result,
                                                 fastapi_response=response,
                                                 session=session)

    def upsert_one_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.post("", status_code=201, response_model=_response_model, dependencies=dependencies)
        async def insert_one_and_support_upsert(
                response: Response,
                query: _request_body_model = Depends(_request_body_model),
                session=Depends(db_session)
        ):
            try:
                stmt = crud_service.upsert(query, unique_list, session)
                _ = session.execute(stmt)
                query_result, = await _ if async_mode else _

            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result
            return await result_parser.upsert_one(response_model=_response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    def upsert_many_api(request_response_model: dict, dependencies):
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        # _response_model = _response_model_list.__dict__['__fields__']['__root__'].type_
        @api.post("", status_code=201, response_model=_response_model, dependencies=dependencies)
        async def insert_many_and_support_upsert(
                response: Response,
                query: _request_body_model = Depends(_request_body_model),
                session=Depends(db_session)
        ):
            try:
                stmt = crud_service.upsert(query, unique_list, session, upsert_one=False)
                query_result = session.execute(stmt)
                query_result = await query_result if async_mode else query_result
            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result

            return await result_parser.upsert_many(response_model=_response_model,
                                                   sql_execute_result=query_result,
                                                   fastapi_response=response,
                                                   session=session)

    def delete_one_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _request_url_model = request_response_model.get('requestUrlParamModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.delete(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        async def delete_one_by_primary_key(response: Response,
                                            query=Depends(_request_query_model),
                                            request_url_param_model=Depends(_request_url_model),
                                            session=Depends(db_session)):
            stmt = crud_service.delete(primary_key=request_url_param_model.__dict__,
                                       delete_args=query.__dict__,
                                       session=session)

            query_result = session.execute(stmt)
            session.expire_all()
            query_result = await query_result if async_mode else query_result
            return await result_parser.delete_one(response_model=_response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    def delete_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _request_url_model = request_response_model.get('requestUrlParamModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.delete('', status_code=200, response_model=_response_model, dependencies=dependencies)
        async def delete_many_by_query(response: Response,
                                       query=Depends(_request_query_model),
                                       session=Depends(db_session)):
            # query_result: CursorResult = crud_service.delete(
            stmt = crud_service.delete(
                delete_args=query.__dict__,
                session=session)

            query_result = session.execute(stmt)
            # if Sqlalchemy
            session.expire_all()
            query_result = await query_result if async_mode else query_result

            return await result_parser.delete_many(response_model=_response_model,
                                                   sql_execute_result=query_result,
                                                   fastapi_response=response,
                                                   session=session)

    def post_redirect_get_api(request_response_model: dict, dependencies):

        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.post("", status_code=303, response_class=Response, dependencies=dependencies)
        async def create_one_and_redirect_to_get_one_api_with_primary_key(
                request: Request,
                insert_args: _request_body_model = Depends(),
                session=Depends(db_session),
        ):

            try:
                stmt = crud_service.insert_one(insert_args.__dict__, session)
                _ = session.execute(stmt)
                query_result, = await _ if async_mode else _

            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result

            return await result_parser.post_redirect_get(response_model=_response_model,
                                                         sql_execute_result=query_result,
                                                         fastapi_request=request,
                                                         session=session)

    def patch_one_api(request_response_model: dict, dependencies):

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.patch(path,
                   status_code=200,
                   response_model=Union[_response_model],
                   dependencies=dependencies)
        async def partial_update_one_by_primary_key(
                response: Response,
                primary_key: _request_url_param_model = Depends(),
                patch_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):
            stmt = crud_service.update(primary_key=primary_key.__dict__,
                                       update_args=patch_data.__dict__,
                                       extra_query=extra_query.__dict__,
                                       session=session)

            query_result = session.execute(stmt)
            session.expire_all()
            query_result = await query_result if async_mode else query_result

            return await result_parser.patch_one(response_model=_response_model,
                                                 sql_execute_result=query_result,
                                                 fastapi_response=response,
                                                 session=session)

    def patch_many_api(request_response_model: dict, dependencies):

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.patch('',
                   status_code=200,
                   response_model=_response_model,
                   dependencies=dependencies)
        async def partial_update_many_by_query(
                response: Response,
                patch_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session)
        ):
            stmt = crud_service.update(update_args=patch_data.__dict__,
                                       extra_query=extra_query.__dict__,
                                       session=session)

            query_result = session.execute(stmt)
            # if SQLALchemy
            session.expire_all()
            query_result = await query_result if async_mode else query_result

            return await result_parser.patch_many(response_model=_response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    def put_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.put(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        async def entire_update_by_primary_key(
                response:Response,
                primary_key: _request_url_param_model = Depends(),
                update_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):
            stmt = crud_service.update(primary_key=primary_key.__dict__,
                                       update_args=update_data.__dict__,
                                       extra_query=extra_query.__dict__,
                                       session=session)
            query_result = session.execute(stmt)
            # if SQLALchemy
            session.expire_all()
            query_result = await query_result if async_mode else query_result

            return await result_parser.update_one(response_model=_response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    def put_many_api(request_response_model: dict, dependencies):
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.put("", status_code=200, response_model=_response_model, dependencies=dependencies)
        async def entire_update_many_by_query(
                response: Response,
                update_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):
            stmt = crud_service.update(update_args=update_data.__dict__,
                                       extra_query=extra_query.__dict__,
                                       session=session)

            query_result = session.execute(stmt)
            # if SQLALchemy
            session.expire_all()
            query_result = await query_result if async_mode else query_result

            return await result_parser.update_many(response_model=_response_model,
                                                   sql_execute_result=query_result,
                                                   fastapi_response=response,
                                                   session=session)

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
        CrudMethods.UPDATE_ONE.value: put_api,
        CrudMethods.UPDATE_MANY.value: put_many_api
    }
    for request_method in methods_dependencies:
        value_of_dict_crud_model = crud_models.get_model_by_request_method(request_method)
        crud_model_of_this_request_methods = value_of_dict_crud_model.keys()
        for crud_model_of_this_request_method in crud_model_of_this_request_methods:
            request_response_model_of_this_request_method = value_of_dict_crud_model[crud_model_of_this_request_method]
            api_register[crud_model_of_this_request_method.value](request_response_model_of_this_request_method,
                                                                  dependencies)

    router.include_router(api, **router_kwargs)
    return router
