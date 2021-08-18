from abc import ABC, abstractmethod
from http import HTTPStatus

from pydantic import parse_obj_as
from starlette.responses import Response, RedirectResponse

from .exceptions import FindOneApiNotRegister


class ResultParseABC(ABC):

    @abstractmethod
    def find_one(self):
        raise NotImplementedError

    @abstractmethod
    def find_many(self):
        raise NotImplementedError

    @abstractmethod
    def update_one(self):
        raise NotImplementedError

    @abstractmethod
    def update_many(self):
        raise NotImplementedError

    @abstractmethod
    def patch_one(self):
        raise NotImplementedError

    @abstractmethod
    def patch_many(self):
        raise NotImplementedError

    @abstractmethod
    def upsert_one(self):
        raise NotImplementedError

    @abstractmethod
    def upsert_many(self):
        raise NotImplementedError

    @abstractmethod
    def delete_one(self):
        raise NotImplementedError

    @abstractmethod
    def delete_many(self):
        raise NotImplementedError

    @abstractmethod
    def post_redirect_get(self):
        raise NotImplementedError


class SQLALchemyResultParse(ResultParseABC):

    def __init__(self, async_model, crud_models, autocommit):
        self.async_mode = async_model
        self.crud_models = crud_models
        self.primary_name = crud_models.PRIMARY_KEY_NAME
        self.autocommit = autocommit

    async def commit(self, session):
        if self.autocommit:
            await session.commit() if self.async_mode else session.commit()

    async def find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        one_row_data = sql_execute_result.one_or_none()
        if one_row_data:
            result = parse_obj_as(response_model, one_row_data[0])
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NO_CONTENT)
        await self.commit(kwargs.get('session'))
        return result

    async def find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result_list = [i for i in sql_execute_result.scalars()]
        result = parse_obj_as(response_model, result_list)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        await self.commit(kwargs.get('session'))
        return result

    async def update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()

        try:
            query_result = next(query_result)
        except StopIteration:
            return Response(status_code=HTTPStatus.NO_CONTENT)

        fastapi_response.headers["x-total-count"] = str(1)
        result = parse_obj_as(response_model, query_result)
        await self.commit(kwargs.get('session'))
        return result

    async def update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        else:
            if not result_list:
                return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        await self.commit(kwargs.get('session'))
        return result

    async def patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        try:
            query_result = next(query_result)
        except StopIteration:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(1)
        result = parse_obj_as(response_model, query_result)
        await self.commit(kwargs.get('session'))
        return result

    async def patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        if not result_list:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        await self.commit(kwargs.get('session'))
        return result

    async def upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(1)
        await self.commit(kwargs.get('session'))
        return result

    async def upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        insert_result_list = sql_execute_result.fetchall()
        result = parse_obj_as(response_model, insert_result_list)
        fastapi_response.headers["x-total-count"] = str(len(insert_result_list))
        await self.commit(kwargs.get('session'))
        return result

    async def delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        if sql_execute_result.rowcount:
            result, = [parse_obj_as(response_model, {self.primary_name: i}) for i in sql_execute_result.scalars()]
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NO_CONTENT)
        await self.commit(kwargs.get('session'))
        return result

    async def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):

        if sql_execute_result.rowcount:
            result_list = [{self.primary_name: i} for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, result_list)
            fastapi_response.headers["x-total-count"] = str(len(result_list))
        else:
            result = Response(status_code=HTTPStatus.NO_CONTENT)
        await self.commit(kwargs.get('session'))
        return result

    async def post_redirect_get(self, *, response_model, sql_execute_result, fastapi_request, **kwargs):
        session = kwargs['session']
        result = parse_obj_as(response_model, sql_execute_result)
        primary_key_field = result.__dict__.pop(self.primary_name, None)
        assert primary_key_field is not None
        redirect_url = fastapi_request.url.path + "/" + str(primary_key_field)
        redirect_end_point = fastapi_request.url.path + "/{" + self.primary_name + "}"
        redirect_url_exist = False
        for route in fastapi_request.app.routes:
            if route.path == redirect_end_point:
                route_request_method, = route.methods
                if route_request_method.upper() == 'GET':
                    redirect_url_exist = True
        if not redirect_url_exist:
            await session.rollback() if self.async_mode else session.rollback()
            raise FindOneApiNotRegister(404,
                                        f'End Point {fastapi_request.url.path}/{ {self.primary_name} }'
                                        f' with GET method not found')
        # FIXME support auth
        await self.commit(kwargs.get('session'))
        return RedirectResponse(redirect_url,
                                status_code=HTTPStatus.SEE_OTHER,
                                )