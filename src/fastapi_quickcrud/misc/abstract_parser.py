import copy
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
from .utils import group_find_many_join


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
    def find_one_sub_func(sql_execute_result, response_model, fastapi_response, **kwargs):
        join = kwargs.get('join_mode', None)
        one_row_data = sql_execute_result.fetchall()
        if not one_row_data:
            return Response('specific data not found', status_code=HTTPStatus.NOT_FOUND)
        # row, = one_row_data
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
        # result = {}
        # for key_, value_ in result__.items():
        #     if '_____' in key_:
        #         key, foreign_column = key_.split('_____')
        #         if key not in result:
        #             result[key] = {foreign_column: value_}
        #         else:
        #             result[key][foreign_column] = value_
        #     else:
        #         result[key_] = value_

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
        # result_list = [i for i in sql_execute_result.scalars()]
        # for table in sql_execute_result:
        #     print(dir(table))
        #     print(table._asdict())
        # FIXME handle NO_CONTENT
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
            deleted_row = dict(sql_execute_result.fetchone())
            result = parse_obj_as(response_model, deleted_row)
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

        deleted_rows = sql_execute_result.fetchall()
        deleted_rows_dict = [dict(deleted_row) for deleted_row in deleted_rows]
        result = parse_obj_as(response_model, deleted_rows_dict)
        fastapi_response.headers["x-total-count"] = str(len(deleted_rows_dict))
        return result

    def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
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
        sql_execute_result, = sql_execute_result
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


class SQLAlchemyTableResultParse(object):

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
        query_result = sql_execute_result.fetchall()
        if not query_result:
            return Response(status_code=HTTPStatus.NO_CONTENT)
        result_list = []
        for result in query_result:
            result_list.append(result)

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
        one_row_data = sql_execute_result.fetchone()
        if one_row_data:
            data_dict = dict(one_row_data)
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
    def find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs):
        # FIXME handle NO_CONTENT
        join = kwargs['join_mode']
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
        # result = parse_obj_as(response_model, result_list)
        return response

    async def async_find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        await self.async_commit(kwargs.get('session'))
        return result

    def find_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.find_many_sub_func(response_model, sql_execute_result, fastapi_response, **kwargs)
        self.commit(kwargs.get('session'))
        return result

    @staticmethod
    def update_one_sub_func(response_model, sql_execute_result, fastapi_response):
        query_result = sql_execute_result.fetchone()
        if not query_result:
            return Response(status_code=HTTPStatus.NOT_FOUND)
        fastapi_response.headers["x-total-count"] = str(1)
        result = parse_obj_as(response_model, dict(query_result))
        return result

    async def async_update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
        return result

    def update_one(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.update_one_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

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
    def upsert_one_sub_func(response_model, sql_execute_result, fastapi_response):
        sql_execute_result = sql_execute_result.fetchone()
        a = dict(sql_execute_result)
        result = parse_obj_as(response_model, a)
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
        delete_result = sql_execute_result.fetchone()
        if not delete_result:
            return Response(status_code=HTTPStatus.NOT_FOUND)

        result = parse_obj_as(response_model, dict(delete_result))
        fastapi_response.headers["x-total-count"] = str(1)
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
        delete_results = sql_execute_result.fetchall()
        if not delete_results:
            return Response(status_code=HTTPStatus.NO_CONTENT)

        result = parse_obj_as(response_model, delete_results)
        fastapi_response.headers["x-total-count"] = str(len(delete_results))
        return result

    def delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
        self.commit(kwargs.get('session'))
        return result

    async def async_delete_many(self, *, response_model, sql_execute_result, fastapi_response, **kwargs):
        result = self.delete_many_sub_func(response_model, sql_execute_result, fastapi_response)
        await self.async_commit(kwargs.get('session'))
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
        sql_execute_result = sql_execute_result.fetchone()
        result = parse_obj_as(response_model, dict(sql_execute_result))
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
