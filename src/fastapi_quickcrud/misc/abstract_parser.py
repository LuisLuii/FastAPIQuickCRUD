from abc import ABC
from http import HTTPStatus
from urllib.parse import urlencode

from pydantic import parse_obj_as
from starlette.responses import Response, RedirectResponse

from .exceptions import FindOneApiNotRegister


# class ResultParserBase(ABC):
#
#     @abstractmethod
#     def find_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def find_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def update_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def update_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def patch_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def patch_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def upsert_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def upsert_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def delete_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def delete_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def post_redirect_get(self):
#         raise NotImplementedError


class SQLAlchemyResultParse(object):

    def __init__(self, async_model, crud_models, autocommit):

        """
        :param async_model: bool
        :param crud_models: pre ready
        :param autocommit: bool
        """

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

    @staticmethod
    async def async_rollback(session):
        await session.rollback()

    @staticmethod
    def rollback(session):
        session.rollback()

    @staticmethod
    def update_many_sub_func(sql_execute_result, fastapi_response, response_model):
        query_result = sql_execute_result.__iter__()
        result_list = []
        for result in query_result:
            result_list.append(result)
        if not result_list:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        return parse_obj_as(response_model, result_list)

    async def async_update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_many_sub_func(sql_execute_result, fastapi_response, response_model)
        await self.async_commit(kwargs.get('session'))
        return result

    async def async_patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_many_sub_func(sql_execute_result, fastapi_response, response_model)
        await self.async_commit(kwargs.get('session'))
        return result

    def patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_many_sub_func(sql_execute_result, fastapi_response, response_model)
        self.commit(kwargs.get('session'))
        return result

    def update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_many_sub_func(sql_execute_result, fastapi_response, response_model)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def find_one_sub_func(sql_execute_result, response_model, fastapi_response):
        one_row_data = sql_execute_result.one_or_none()
        if one_row_data:
            row, = one_row_data
            data_dict = row.__dict__
            result = parse_obj_as(response_model, data_dict)
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response('specific data not found', status_code=HTTPStatus.NOT_FOUND)
        return result

    async def async_find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_one_sub_func(sql_execute_result, response_model, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_one_sub_func(sql_execute_result, response_model, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def find_many_sub_func(response_model, sql_execute_result, fastapi_response):
        # FIXME handle NO_CONTENT
        result_list = [i.__dict__ for i in sql_execute_result.scalars()]
        result = parse_obj_as(response_model, result_list)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        return result

    async def async_find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def update_one_sub_func(response_model, sql_execute_result, fastapi_response):
        query_result = sql_execute_result.__iter__()
        try:
            query_result = next(query_result)
        except StopIteration:
            return Response(status_code=HTTPStatus.NOT_FOUND)
        fastapi_response.headers["x-total-count"] = str(1)
        result = parse_obj_as(response_model, query_result)
        return result

    async def async_update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    async def async_patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def upsert_one_sub_func(response_model, sql_execute_result, fastapi_response):
        sql_execute_result, = sql_execute_result
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(1)
        return result

    async def async_upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.upsert_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def upsert_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.upsert_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def upsert_many_sub_func(response_model, sql_execute_result, fastapi_response):
        insert_result_list = sql_execute_result.fetchall()
        result = parse_obj_as(response_model, insert_result_list)
        fastapi_response.headers["x-total-count"] = str(len(insert_result_list))
        return result

    async def async_upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.upsert_many_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def upsert_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.upsert_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    def delete_one_sub_func(self, response_model, sql_execute_result, fastapi_response):
        if sql_execute_result.rowcount:
            deleted_primary_key_value, = [i for i in sql_execute_result.scalars()]
            result = parse_obj_as(response_model, {self.primary_name: deleted_primary_key_value})
            fastapi_response.headers["x-total-count"] = str(1)
        else:
            result = Response(status_code=HTTPStatus.NOT_FOUND)
        return result

    def delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def delete_many_sub_func(self, response_model, sql_execute_result, fastapi_response):
        if not sql_execute_result.rowcount:
            return Response(status_code=HTTPStatus.NO_CONTENT)

        result_list = [{self.primary_name: i} for i in sql_execute_result.scalars()]
        result = parse_obj_as(response_model, result_list)
        fastapi_response.headers["x-total-count"] = str(len(result_list))
        return result

    def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
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
        redirect_url += f'?{urlencode(header_dict)}'
        await self.async_commit(session)
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
