import copy
from http import HTTPStatus
from urllib.parse import urlencode
from pydantic import parse_obj_as
from starlette.responses import Response, RedirectResponse

from .utils import group_find_many_join
from .exceptions import FindOneApiNotRegister


class SQLAlchemyGeneralSQLeResultParse(object):

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
        await session.flush()
        if self.autocommit:
            await session.commit()

    def commit(self, session):
        session.flush()
        if self.autocommit:
            session.commit()

    async def async_delete(self, session, data):
        await session.delete(data)

    def delete(self, session, data):
        session.delete(data)

    def update_data_model(self, data, update_args):
        for update_arg_name, update_arg_value in update_args.items():
            setattr(data, update_arg_name, update_arg_value)
        return data

    @staticmethod
    async def async_rollback(session):
        await session.rollback()

    @staticmethod
    def rollback(session):
        session.rollback()

    @staticmethod
    def _response_builder(sql_execute_result, fastapi_response, response_model):
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(len(sql_execute_result) if isinstance(sql_execute_result, list)
                                                        else '1')
        return result

    # async def async_update_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     result = self._response_builder(sql_execute_result, fastapi_response, response_model)
    #     await self.async_commit(kwargs.get('session'))
    #     return result
    #
    # async def async_patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     result = self._response_builder(sql_execute_result, fastapi_response, response_model)
    #     await self.async_commit(kwargs.get('session'))
    #     return result
    #
    # def patch_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     result = self._response_builder(sql_execute_result, fastapi_response, response_model)
    #     self.commit(kwargs.get('session'))
    #     return result

    def update_func(self, response_model, sql_execute_result, fastapi_response, update_args, update_one):
        if not isinstance(sql_execute_result, list):
            sql_execute_result = [sql_execute_result]
        tmp = []
        for i in sql_execute_result:
            tmp.append(self.update_data_model(i, update_args=update_args))

        if not update_one:
            sql_execute_result = tmp
        else:
            sql_execute_result, = tmp
        return self._response_builder(response_model=response_model,
                                      sql_execute_result=sql_execute_result,
                                      fastapi_response=fastapi_response)

    def update(self, *, response_model, sql_execute_result, fastapi_response, update_args, **kwargs):
        session = kwargs.get('session')
        update_one = kwargs.get('update_one')
        result = self.update_func(response_model, sql_execute_result, fastapi_response, update_args, update_one)
        self.commit(session)
        return result

    async def async_update(self, *, response_model, sql_execute_result, fastapi_response, update_args, **kwargs):
        session = kwargs.get('session')
        update_one = kwargs.get('update_one')
        result = self.update_func(response_model, sql_execute_result, fastapi_response, update_args, update_one)
        await self.async_commit(session)
        return result

    @staticmethod
    def find_one_sub_func(sql_execute_result, response_model, fastapi_response, **kwargs):
        join = kwargs.get('join_mode', None)

        one_row_data = sql_execute_result.fetchall()
        if not one_row_data:
            return Response('specific data not found', status_code=HTTPStatus.NOT_FOUND)
        response = []
        for i in one_row_data:
            i = dict(i)
            result__ = copy.deepcopy(i)
            tmp = {}
            for key_, value_ in result__.items():
                if '_____' in key_:
                    key, foreign_column = key_.split('_____')
                    if key not in tmp:
                        tmp[key] = {foreign_column: value_}
                    else:
                        tmp[key][foreign_column] = value_
                else:
                    tmp[key_] = value_
            response.append(tmp)
        if join:
            response = group_find_many_join(response)
        if isinstance(response, list):
            response = response[0]
        fastapi_response.headers["x-total-count"] = str(1)
        return response

    async def async_find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_one_sub_func(sql_execute_result, response_model, fastapi_response, **kwargs)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_one_sub_func(sql_execute_result, response_model, fastapi_response, **kwargs)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs):
        join = kwargs.get('join_mode', None)
        result = sql_execute_result.fetchall()
        if not result:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        response = []
        for i in result:
            i = dict(i)
            result__ = copy.deepcopy(i)
            tmp = {}
            for key_, value_ in result__.items():
                if '_____' in key_:
                    key, foreign_column = key_.split('_____')
                    if key not in tmp:
                        tmp[key] = {foreign_column: value_}
                    else:
                        tmp[key][foreign_column] = value_
                else:
                    tmp[key_] = value_
            response.append(tmp)

        fastapi_response.headers["x-total-count"] = str(len(response))
        if join:
            response = group_find_many_join(response)
        response = parse_obj_as(response_model, response)
        return response

    async def async_find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        self.commit(kwargs.get('session'))
        return result

    # @staticmethod
    # def update_one_sub_func(response_model, sql_execute_result, fastapi_response):
    #     result = parse_obj_as(response_model, sql_execute_result)
    #     fastapi_response.headers["x-total-count"] = str(1)
    #     return result
    #
    # async def async_update_one(self, *, response_model, sql_execute_result, fastapi_response, update_args, **kwargs):
    #     session = kwargs.get('session')
    #     if not sql_execute_result:
    #         return Response(status_code=HTTPStatus.NOT_FOUND)
    #     data = self.update_data_model(sql_execute_result, update_args=update_args)
    #     result = self.update_one_sub_func(response_model, data, fastapi_response)
    #     await self.commit(session)
    #     return result
    #
    # def update_one(self, *, response_model, sql_execute_result, fastapi_response, update_args, **kwargs):
    #     session = kwargs.get('session')
    #     if not sql_execute_result:
    #         return Response(status_code=HTTPStatus.NOT_FOUND)
    #     data = self.update_data_model(sql_execute_result, update_args=update_args)
    #     result = self.update_one_sub_func(response_model, data, fastapi_response)
    #     self.commit(session)
    #     return result

    # async def async_patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
    #     await self.async_commit(kwargs.get('session'))
    #     return result
    #
    # def patch_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
    #     result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
    #     self.commit(kwargs.get('session'))
    #     return result

    @staticmethod
    def create_one_sub_func(response_model, sql_execute_result, fastapi_response):
        inserted_data, = sql_execute_result
        result = parse_obj_as(response_model, inserted_data)
        fastapi_response.headers["x-total-count"] = str(1)
        return result

    async def async_create_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.create_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def create_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.create_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def create_many_sub_func(response_model, sql_execute_result, fastapi_response):
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(len(sql_execute_result))
        return result

    async def async_create_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.create_many_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def create_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.create_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def upsert_one_sub_func(response_model, sql_execute_result, fastapi_response):
        sql_execute_result = sql_execute_result.fetchone()
        result = parse_obj_as(response_model, dict(sql_execute_result))
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

    def delete_one_sub_func(self, response_model, sql_execute_result, fastapi_response, **kwargs):
        if not sql_execute_result:
            return Response(status_code=HTTPStatus.NOT_FOUND)
        result = parse_obj_as(response_model, sql_execute_result)
        fastapi_response.headers["x-total-count"] = str(1)
        return result

    def delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        session = kwargs.get('session')
        if sql_execute_result:
            self.delete(session, sql_execute_result)
        result = self.delete_one_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        self.commit(session)
        return result

    async def async_delete_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        session = kwargs.get('session')
        if sql_execute_result:
            self.delete(session, sql_execute_result)
        result = self.delete_one_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        await self.async_commit(session)
        return result

    def delete_many_sub_func(self, response_model, sql_execute_result, fastapi_response):
        if not sql_execute_result:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        deleted_rows = sql_execute_result
        result = parse_obj_as(response_model, deleted_rows)
        fastapi_response.headers["x-total-count"] = str(len(deleted_rows))
        return result

    def delete_many(self, *, response_model, sql_execute_results, fastapi_response, **kwargs):
        session = kwargs.get('session')
        if sql_execute_results:
            for sql_execute_result in sql_execute_results:
                self.delete(session, sql_execute_result)
        result = self.delete_many_sub_func(response_model, sql_execute_results, fastapi_response)
        self.commit(session)
        return result

    async def async_delete_many(self, *, response_model, sql_execute_results, fastapi_response, **kwargs):
        session = kwargs.get('session')
        if sql_execute_results:
            for sql_execute_result in sql_execute_results:
                await self.async_delete(session, sql_execute_result)
        result = self.delete_many_sub_func(response_model, sql_execute_results, fastapi_response)
        await self.async_commit(session)
        return result

    def has_end_point(self, fastapi_request) -> bool:
        redirect_end_point = fastapi_request.url.path + "/{" + self.primary_name + "}"
        redirect_url_exist = False
        for route in fastapi_request.app.routes:
            if route.path == redirect_end_point:
                route_request_method, = route.methods
                if route_request_method.upper() == 'GET':
                    redirect_url_exist = True
        return redirect_url_exist

    def post_redirect_get_sub_func(self, response_model, sql_execute_result, fastapi_request):
        result = parse_obj_as(response_model, sql_execute_result)
        primary_key_field = result.__dict__.pop(self.primary_name, None)
        assert primary_key_field is not None
        redirect_url = fastapi_request.url.path + "/" + str(primary_key_field)
        return redirect_url

    def get_post_redirect_get_url(self, response_model, sql_execute_result, fastapi_request):
        redirect_url = self.post_redirect_get_sub_func(response_model, sql_execute_result, fastapi_request)
        header_dict = {i[0].decode("utf-8"): i[1].decode("utf-8") for i in fastapi_request.headers.__dict__['_list']}
        redirect_url += f'?{urlencode(header_dict)}'
        return redirect_url

    async def async_post_redirect_get(self, *, response_model, sql_execute_result, fastapi_request, **kwargs):
        session = kwargs['session']
        if not self.has_end_point(fastapi_request):
            await self.async_rollback(session)
            raise FindOneApiNotRegister(404,
                                        f'End Point {fastapi_request.url.path}/{ {self.primary_name} }'
                                        f' with GET method not found')
        redirect_url = self.get_post_redirect_get_url(response_model, sql_execute_result, fastapi_request)
        await self.async_commit(session)
        return RedirectResponse(redirect_url,
                                status_code=HTTPStatus.SEE_OTHER
                                )

    def post_redirect_get(self, *, response_model, sql_execute_result, fastapi_request, **kwargs):
        session = kwargs['session']
        if not self.has_end_point(fastapi_request):
            self.rollback(session)
            raise FindOneApiNotRegister(404,
                                        f'End Point {fastapi_request.url.path}/{ {self.primary_name} }'
                                        f' with GET method not found')
        redirect_url = self.get_post_redirect_get_url(response_model, sql_execute_result, fastapi_request)
        self.commit(session)
        return RedirectResponse(redirect_url,
                                status_code=HTTPStatus.SEE_OTHER
                                )
