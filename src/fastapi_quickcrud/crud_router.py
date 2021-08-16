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
    BaseModel, \
    parse_obj_as
from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from .crud_service import CrudService
from .misc.crud_model import CRUDModel
from .misc.exceptions import FindOneApiNotRegister, PrimaryMissing
from .misc.type import CrudMethods


CRUDModelType = TypeVar("CRUDModelType", bound=BaseModel)
CompulsoryQueryModelType = TypeVar("CompulsoryQueryModelType", bound=BaseModel)
OnConflictModelType = TypeVar("OnConflictModelType", bound=BaseModel)


def crud_router(
        *,
        db_session,
        crud_service: CrudService,
        crud_models: CRUDModel,
        dependencies: List[callable],
        **router_kwargs: Any) -> APIRouter:
    """

    :param db_session: db_session
    :param crud_service:
    :param crud_models:
    :param router_kwargs:  Optional arguments that ``APIRouter().include_router`` takes.
    :return:
    """
    api = APIRouter()
    methods_dependencies = crud_models.get_available_request_method()
    primary_name = crud_models.PRIMARY_KEY_NAME
    if not primary_name:
        raise PrimaryMissing("primary key is required")
    path = '/{' + primary_name + '}'
    unique_list: List[str] = crud_models.UNIQUE_LIST

    dependencies = [Depends(dep) for dep in dependencies]
    router = APIRouter()

    def find_one_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.get(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        def get_one_by_primary_key(response: Response,
                                   url_param: _request_url_param_model = Depends(),
                                   query=Depends(_request_query_model),
                                   session=Depends(db_session)):

            query_result: ChunkedIteratorResult = crud_service.get_one(filter_args=query.__dict__,
                                                                       extra_args=url_param.__dict__,
                                                                       session=session)
            one_row_data = query_result.one_or_none()
            if one_row_data:
                result = parse_obj_as(_response_model, one_row_data[0])
                response.headers["x-total-count"] = str(1)
            else:
                result = Response(status_code=HTTPStatus.NO_CONTENT)
            session.commit()
            return result

    def find_many_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.get("", response_model=_response_model, dependencies=dependencies)
        def get_many(response: Response,
                     query=Depends(_request_query_model),
                     session=Depends(
                         db_session)
                     ):
            query_dict = query.__dict__
            limit = query_dict.pop('limit', None)
            offset = query_dict.pop('offset', None)
            order_by_columns = query_dict.pop('order_by_columns', None)
            query_result: ChunkedIteratorResult = crud_service.get_many(
                filter_args=query_dict,
                limit=limit,
                offset=offset, order_by_columns=order_by_columns,
                session=session)

            result_list = [i for i in query_result.scalars()]
            result = parse_obj_as(_response_model, result_list)
            response.headers["x-total-count"] = str(len(result_list))
            session.commit()
            return result

    def upsert_one_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.post("", status_code=201, response_model=_response_model, dependencies=dependencies)
        def insert_one_and_support_upsert(
                response: Response,
                query: _request_body_model = Depends(_request_body_model),
                session=Depends(db_session)
        ):
            try:
                query_result, = crud_service.upsert(query, unique_list, session)
            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result
            result = parse_obj_as(_response_model, query_result)
            response.headers["x-total-count"] = str(1)
            session.commit()
            return result

    def upsert_many_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        # _response_model = _response_model_list.__dict__['__fields__']['__root__'].type_
        @api.post("", status_code=201, response_model=_response_model, dependencies=dependencies)
        def insert_many_and_support_upsert(
                response: Response,
                query: _request_body_model = Depends(_request_body_model),
                session=Depends(db_session)
        ):
            try:
                query_result: CursorResult = crud_service.upsert(query, unique_list, session, upsert_one=False)
            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result
            insert_result_list = query_result.fetchall()
            req = parse_obj_as(_response_model, insert_result_list)
            response.headers["x-total-count"] = str(len(insert_result_list))
            session.commit()
            return req

    def delete_one_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _request_url_model = request_response_model.get('requestUrlParamModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.delete(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        def delete_one_by_primary_key(response: Response,
                                      query=Depends(_request_query_model),
                                      request_url_param_model=Depends(_request_url_model),
                                      session=Depends(db_session)):

            query_result: CursorResult = crud_service.delete(primary_key=request_url_param_model.__dict__,
                                                             delete_args=query.__dict__,
                                                             session=session)
            if query_result.rowcount:
                result, = [parse_obj_as(_response_model, {primary_name: i}) for i in query_result.scalars()]
                response.headers["x-total-count"] = str(1)
            else:
                result = Response(status_code=HTTPStatus.NO_CONTENT)
            session.commit()
            return result

    def delete_many_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _request_url_model = request_response_model.get('requestUrlParamModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.delete('', status_code=200, response_model=_response_model, dependencies=dependencies)
        def delete_many_by_query(response: Response,
                                 query=Depends(_request_query_model),
                                 session=Depends(db_session)):

            query_result: CursorResult = crud_service.delete(
                delete_args=query.__dict__,
                session=session)
            if query_result.rowcount:
                # result = [parse_obj_as(_response_model, {primary_name: i}) for i in query_result.scalars()]
                result_list = [{primary_name: i}for i in query_result.scalars()]
                result = parse_obj_as(_response_model,result_list)
                response.headers["x-total-count"] = str(len(result_list))
            else:
                result = Response(status_code=HTTPStatus.NO_CONTENT)
            session.commit()
            return result

    def post_redirect_get_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []

        _request_body_model = request_response_model.get('requestBodyModel', None)
        _response_model = request_response_model.get('responseModel', None)

        @api.post("", status_code=303, response_class=Response, dependencies=dependencies)
        def create_one_and_redirect_to_get_one_api_with_primary_key(
                request: Request,
                insert_args: _request_body_model = Depends(),
                session=Depends(db_session),
        ):

            try:
                query_result: List[CursorResult] = crud_service.insert_one(insert_args.__dict__, session)
            except IntegrityError as e:
                err_msg, = e.orig.args
                if 'duplicate key value violates unique constraint' not in err_msg:
                    raise e
                result = Response(status_code=HTTPStatus.CONFLICT)
                return result
            query_result_, = query_result
            result = parse_obj_as(_response_model, query_result_)

            primary_key_field = result.__dict__.pop(primary_name, None)
            assert primary_key_field is not None
            redirect_url = request.url.path + "/" + str(primary_key_field)
            redirect_url_exist = False
            redirect_end_point = request.url.path + "/{" + primary_name + "}"
            for route in request.app.routes:
                if route.path == redirect_end_point:
                    route_request_method, = route.methods
                    if route_request_method.upper() == 'GET':
                        redirect_url_exist = True
            if not redirect_url_exist:
                raise FindOneApiNotRegister(404,
                                            f'EndPoint {request.url.path}/{ {primary_name} }  with GET method not found')
            # FIXME support auth
            # headers = request.headers.__dict__
            # print(request.headers.__dir__())
            # headers.pop('content-length')
            # headers['referer'] = request.url
            result = RedirectResponse(redirect_url,
                                      status_code=HTTPStatus.SEE_OTHER,
                                      # headers=request.headers
                                      )
            session.commit()
            return result

    def patch_one_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.patch(path,
                   status_code=200,
                   response_model=Union[_response_model],
                   dependencies=dependencies)
        def partial_update_one_by_primary_key(
                primary_key: _request_url_param_model = Depends(),
                patch_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):
            # FIXME unify the return
            query_result = crud_service.update(primary_key=primary_key.__dict__,
                                               update_args=patch_data.__dict__,
                                               extra_query=extra_query.__dict__,
                                               session=session)
            try:
                query_result = next(query_result)
            except StopIteration:
                return Response(status_code=HTTPStatus.NO_CONTENT)

            result = parse_obj_as(_response_model, query_result)
            session.commit()
            return result

    def patch_many_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []

        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.patch('',
                   status_code=200,
                   response_model=_response_model,
                   dependencies=dependencies)
        def partial_update_many_by_query(
                patch_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):
            query_result = crud_service.update(update_args=patch_data.__dict__,
                                               extra_query=extra_query.__dict__,
                                               session=session)
            result_list = []
            for result in query_result:
                result_list.append(result)
            else:
                if not result_list:
                    return Response(status_code=HTTPStatus.NO_CONTENT)

            result = parse_obj_as(_response_model, result_list)
            session.commit()
            return result

    def put_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.put(path, status_code=200, response_model=_response_model, dependencies=dependencies)
        def entire_update_by_primary_key(
                primary_key: _request_url_param_model = Depends(),
                update_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):

            query_result = crud_service.update(primary_key=primary_key.__dict__,
                                               update_args=update_data.__dict__,
                                               extra_query=extra_query.__dict__,
                                               session=session)
            try:
                query_result = next(query_result)
            except StopIteration:
                return Response(status_code=HTTPStatus.NO_CONTENT)

            result = parse_obj_as(_response_model, query_result)
            session.commit()
            return result

    def put_many_api(request_response_model: dict, dependencies=None):
        if dependencies == None:
            dependencies = []
        _request_query_model = request_response_model.get('requestQueryModel', None)
        _response_model = request_response_model.get('responseModel', None)
        _request_body_model = request_response_model.get('requestBodyModel', None)
        _request_url_param_model = request_response_model.get('requestUrlParamModel', None)

        @api.put("", status_code=200, response_model=_response_model, dependencies=dependencies)
        def entire_update_many_by_query(
                update_data: _request_body_model = Depends(),
                extra_query: _request_query_model = Depends(),
                session=Depends(db_session),
        ):

            query_result = crud_service.update(update_args=update_data.__dict__,
                                               extra_query=extra_query.__dict__,
                                               session=session)
            result_list = []
            for result in query_result:
                result_list.append(result)
            else:
                if not result_list:
                    return Response(status_code=HTTPStatus.NO_CONTENT)

            result = parse_obj_as(_response_model, result_list)
            session.commit()
            return result

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
            api_register[crud_model_of_this_request_method.value](request_response_model_of_this_request_method, dependencies)

    router.include_router(api, **router_kwargs)
    return router
