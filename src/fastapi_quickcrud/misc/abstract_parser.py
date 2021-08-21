from abc import ABC, abstractmethod
from http import HTTPStatus
from urllib.parse import urlencode

from pydantic import parse_obj_as
from starlette.responses import Response, RedirectResponse

from .exceptions import FindOneApiNotRegister


class ResultParserBase(ABC):

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


class SQLALchemyResultParse(ResultParserBase):

    def __init__(self, async_model, crud_models, autocommit):
        self.async_mode = async_model
        self.crud_models = crud_models
        self.primary_name = crud_models.PRIMARY_KEY_NAME
        self.autocommit = autocommit

    async def async_commit(self, session):
        if self.autocommit:
            await session.commit()

    def commit(self, session):
        if self.autocommit:
            session.commit()

    async def async_rollback(self, session):
        await session.rollback()

    def rollback(self, session):
        session.rollback()

    async def async_find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        one_row_data = sql_execute_result.one_or_none()
        if one_row_data:
            row, = one_row_data
            data_dict = row.__dict__
            result = parse_obj_as(response_model, data_dict)
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NOT_FOUND)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        one_row_data = sql_execute_result.one_or_none()
        if one_row_data:
            row, = one_row_data
            data_dict = row.__dict__
            result = parse_obj_as(response_model, data_dict)
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response('specific data not found',status_code=HTTPStatus.NOT_FOUND)
        self.commit(kwargs.get('session'))
        return result

    async def async_find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        # FIXME handle NO_CONTENT
        result_list = [i.__dict__ for i in sql_execute_result.scalars()]
        result = parse_obj_as(response_model, result_list)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        await self.async_commit(kwargs.get('session'))
        return result

    def find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result_list = [i.__dict__ for i in sql_execute_result.scalars()]
        result = parse_obj_as(response_model, result_list)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        self.commit(kwargs.get('session'))
        return result

    async def async_update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()

        try:
            query_result = next(query_result)
            fastapi_response.headers["x-total-count"] = str(1)
            result = parse_obj_as(response_model, query_result)
            await self.async_commit(kwargs.get('session'))
        except StopIteration:
            result = Response(status_code=HTTPStatus.NOT_FOUND)

        return result

    def update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()

        try:
            query_result = next(query_result)
            fastapi_response.headers["x-total-count"] = str(1)
            result = parse_obj_as(response_model, query_result)
            self.commit(kwargs.get('session'))
        except StopIteration:
            result = Response(status_code=HTTPStatus.NOT_FOUND)

        return result

    async def async_update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        else:
            if not result_list:
                return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        await self.async_commit(kwargs.get('session'))
        return result

    def update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        else:
            if not result_list:
                return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        self.commit(kwargs.get('session'))
        return result

    async def async_patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        try:
            query_result = next(query_result)
            fastapi_response.headers["x-total-count"] = str(1)
            result = parse_obj_as(response_model, query_result)
            await self.async_commit(kwargs.get('session'))
        except StopIteration:
            result = Response(status_code=HTTPStatus.NOT_FOUND)

        return result

    def patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        try:
            query_result = next(query_result)
            fastapi_response.headers["x-total-count"] = str(1)
            result = parse_obj_as(response_model, query_result)
            self.commit(kwargs.get('session'))
        except StopIteration:
            result = Response(status_code=HTTPStatus.NOT_FOUND)

        return result

    async def async_patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        if not result_list:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        await self.async_commit(kwargs.get('session'))
        return result

    def patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        if not result_list:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        result = parse_obj_as(response_model, result_list)
        self.commit(kwargs.get('session'))
        return result

    async def async_upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        sql_execute_result, = sql_execute_result
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(1)
        await self.async_commit(kwargs.get('session'))
        return result

    def upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        sql_execute_result, = sql_execute_result
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(1)
        self.commit(kwargs.get('session'))
        return result

    async def async_upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        insert_result_list = sql_execute_result.fetchall()
        result = parse_obj_as(response_model, insert_result_list)
        fastapi_response.headers["x-total-count"] = str(len(insert_result_list))
        await self.async_commit(kwargs.get('session'))
        return result

    def upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        insert_result_list = sql_execute_result.fetchall()
        result = parse_obj_as(response_model, insert_result_list)
        fastapi_response.headers["x-total-count"] = str(len(insert_result_list))
        self.commit(kwargs.get('session'))
        return result

    def delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        if sql_execute_result.rowcount:
            deleted_primary_key_value, = [i for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, {self.primary_name: deleted_primary_key_value})
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NOT_FOUND)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        if sql_execute_result.rowcount:
            deleted_primary_key_value, = [i for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, {self.primary_name: deleted_primary_key_value})
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NOT_FOUND)
        await self.async_commit(kwargs.get('session'))
        return result

    def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):

        if sql_execute_result.rowcount:
            result_list = [{self.primary_name: i} for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, result_list)
            fastapi_response.headers["x-total-count"] = str(len(result_list))
        else:
            result = Response(status_code=HTTPStatus.NO_CONTENT)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):

        if sql_execute_result.rowcount:
            result_list = [{self.primary_name: i} for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, result_list)
            fastapi_response.headers["x-total-count"] = str(len(result_list))
        else:
            result = Response(status_code=HTTPStatus.NO_CONTENT)
        await self.async_commit(kwargs.get('session'))
        return result

    async def async_post_redirect_get(self, *, response_model, sql_execute_result, fastapi_request, **kwargs):
        sql_execute_result, = sql_execute_result
        session = kwargs['session']
        result = parse_obj_as(response_model, sql_execute_result)
        primary_key_field = result.__dict__.pop(self.primary_name, None)
        assert primary_key_field is not None
        redirect_url = fastapi_request.url.path + "/" + str(primary_key_field)
        redirect_end_point = fastapi_request.url.path + "/{" + self.primary_name + "}"
        redirect_url_exist = False
        header_dict = {i[0].decode("utf-8"): i[1].decode("utf-8") for i in fastapi_request.headers.__dict__['_list']}
        for route in fastapi_request.app.routes:
            if route.path == redirect_end_point:
                route_request_method, = route.methods
                if route_request_method.upper() == 'GET':
                    redirect_url_exist = True
        if not redirect_url_exist:
            await self.async_rollback(session)
            raise FindOneApiNotRegister(404,
                                        f'End Point {fastapi_request.url.path}/{ {self.primary_name} }'
                                        f' with GET method not found')
        await self.async_commit(session)
        redirect_url += f'?{urlencode(header_dict)}'
        return RedirectResponse(redirect_url,
                                status_code=HTTPStatus.SEE_OTHER
                                )

    def post_redirect_get(self, *, response_model, sql_execute_result, fastapi_request, **kwargs):
        sql_execute_result, = sql_execute_result
        session = kwargs['session']
        result = parse_obj_as(response_model, sql_execute_result)
        primary_key_field = result.__dict__.pop(self.primary_name, None)
        assert primary_key_field is not None
        redirect_url = fastapi_request.url.path + "/" + str(primary_key_field)
        redirect_end_point = fastapi_request.url.path + "/{" + self.primary_name + "}"
        redirect_url_exist = False
        header_dict = {i[0].decode("utf-8"): i[1].decode("utf-8") for i in fastapi_request.headers.__dict__['_list']}
        for route in fastapi_request.app.routes:
            if route.path == redirect_end_point:
                route_request_method, = route.methods
                if route_request_method.upper() == 'GET':
                    redirect_url_exist = True
        if not redirect_url_exist:
            self.rollback(session)
            raise FindOneApiNotRegister(404,
                                        f'End Point {fastapi_request.url.path}/{ {self.primary_name} }'
                                        f' with GET method not found')
        self.commit(session)
        redirect_url += f'?{urlencode(header_dict)}'
        return RedirectResponse(redirect_url,
                                status_code=HTTPStatus.SEE_OTHER
                                )



class DatabasesResultParserBase(ABC):
    def __init__(self):
        raise NotImplementedError

    # def __init__(self, async_model, crud_models, autocommit):
    #     self.async_mode = async_model
    #     self.crud_models = crud_models
    #     self.primary_name = crud_models.PRIMARY_KEY_NAME
    #     self.autocommit = autocommit
    #
    # async def async_commit(self, session):
    #     if self.autocommit:
    #         await session.commit()
    #
    # async def async_find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     if not sql_execute_result:
    #         return Response('specific data not found',status_code=HTTPStatus.NOT_FOUND)
    #     result = parse_obj_as(response_model, dict(sql_execute_result))
    #     fastapi_response.headers["x-total-count"] = str(1)
    #
    #     await self.async_commit(kwargs.get('session'))
    #     return result
    #
    # async def async_find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     # sql_execute_result = [] if no data
    #     result_list = [dict(i) for i in sql_execute_result]
    #     result = parse_obj_as(response_model, result_list)
    #     fastapi_response.headers["x-total-count"] = str(len(result_list))
    #     await self.async_commit(kwargs.get('session'))
    #     return result
    #
    # def update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
    #
    # def post_redirect_get(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     raise NotImplementedError
    #
