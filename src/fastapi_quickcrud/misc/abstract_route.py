from abc import abstractmethod, ABC
from http import HTTPStatus
from typing import Union

from fastapi import \
    Depends, \
    Response
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request


class SQLAlchemyGeneralSQLBaseRouteSource(ABC):
    """ This route will support the SQL SQLAlchemy dialects. """

    @classmethod
    def find_one(cls, api,
                 *,
                 path,
                 query_service,
                 parsing_service,
                 execute_service,
                 async_mode,
                 response_model,
                 dependencies,
                 request_url_param_model,
                 request_query_model,
                 db_session):

        if not async_mode:
            @api.get(path, status_code=200, response_model=response_model, dependencies=dependencies)
            def get_one_by_primary_key(response: Response,
                                       request: Request,
                                       url_param=Depends(request_url_param_model),
                                       query=Depends(request_query_model),
                                       session=Depends(db_session)):

                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_one(filter_args=query.__dict__,
                                             extra_args=url_param.__dict__,
                                             join_mode=join)
                query_result = execute_service.execute(session, stmt)
                response_result = parsing_service.find_one(response_model=response_model,
                                                           sql_execute_result=query_result,
                                                           fastapi_response=response,
                                                           session=session,
                                                           join_mode=join)
                return response_result
        else:
            @api.get(path, status_code=200, response_model=response_model, dependencies=dependencies)
            async def async_get_one_by_primary_key(response: Response,
                                                   request: Request,
                                                   url_param=Depends(request_url_param_model),
                                                   query=Depends(request_query_model),
                                                   session=Depends(db_session)):

                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_one(filter_args=query.__dict__,
                                             extra_args=url_param.__dict__,
                                             join_mode=join)
                query_result = await execute_service.async_execute(session, stmt)

                response_result = await parsing_service.async_find_one(response_model=response_model,
                                                                       sql_execute_result=query_result,
                                                                       fastapi_response=response,
                                                                       session=session,
                                                                       join_mode=join)
                return response_result

    @classmethod
    def find_many(cls, api, *,
                  query_service,
                  parsing_service,
                  execute_service,
                  async_mode,
                  path,
                  response_model,
                  dependencies,
                  request_query_model,
                  db_session):

        if async_mode:
            @api.get(path, dependencies=dependencies, response_model=response_model)
            async def async_get_many(response: Response,
                                     request: Request,
                                     query=Depends(request_query_model),
                                     session=Depends(
                                         db_session)
                                     ):
                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_many(query=query.__dict__, join_mode=join)

                query_result = await execute_service.async_execute(session, stmt)

                parsed_response = await parsing_service.async_find_many(response_model=response_model,
                                                                        sql_execute_result=query_result,
                                                                        fastapi_response=response,
                                                                        join_mode=join,
                                                                        session=session)
                return parsed_response
        else:
            @api.get(path, dependencies=dependencies, response_model=response_model)
            def get_many(response: Response,
                         request: Request,
                         query=Depends(request_query_model),
                         session=Depends(
                             db_session)
                         ):
                join = query.__dict__.pop('join_foreign_table', None)

                stmt = query_service.get_many(query=query.__dict__, join_mode=join)
                query_result = execute_service.execute(session, stmt)
                parsed_response = parsing_service.find_many(response_model=response_model,
                                                            sql_execute_result=query_result,
                                                            fastapi_response=response,
                                                            join_mode=join,
                                                            session=session)
                return parsed_response

    @abstractmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @abstractmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):

        raise NotImplementedError

    @classmethod
    def create_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        if async_mode:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_one(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                # stmt = query_service.create(insert_arg=query)

                new_inserted_data = query_service.create(insert_arg=query.__dict__)

                execute_service.add_all(session, new_inserted_data)
                try:
                    await execute_service.async_flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return await parsing_service.async_create_one(response_model=response_model,
                                                              sql_execute_result=new_inserted_data,
                                                              fastapi_response=response,
                                                              session=session)
        else:

            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_one(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):

                new_inserted_data = query_service.create(insert_arg=query.__dict__)

                execute_service.add_all(session, new_inserted_data)

                try:
                    execute_service.flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return parsing_service.create_one(response_model=response_model,
                                                  sql_execute_result=new_inserted_data,
                                                  fastapi_response=response,
                                                  session=session)

    @classmethod
    def create_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):

        if async_mode:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_many(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                inserted_data = query_service.create(insert_arg=query.__dict__,
                                                     create_one=False)

                execute_service.add_all(session, inserted_data)

                try:
                    await execute_service.async_flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return await parsing_service.async_create_many(response_model=response_model,
                                                               sql_execute_result=inserted_data,
                                                               fastapi_response=response,
                                                               session=session)
        else:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_many(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):

                # inserted_data = query.__dict__['insert']
                update_list = query.__dict__
                inserted_data = query_service.create(insert_arg=update_list,
                                                     create_one=False)

                execute_service.add_all(session, inserted_data)

                try:
                    execute_service.flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return parsing_service.create_many(response_model=response_model,
                                                   sql_execute_result=inserted_data,
                                                   fastapi_response=response,
                                                   session=session)

    @classmethod
    def delete_one(cls, api, *,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   path,
                   response_model,
                   dependencies,
                   request_query_model,
                   request_url_model,
                   db_session, ):

        if async_mode:
            @api.delete(path, status_code=200, response_model=response_model, dependencies=dependencies)
            async def async_delete_one_by_primary_key(response: Response,
                                                      request: Request,
                                                      query=Depends(request_query_model),
                                                      request_url_param_model=Depends(request_url_model),
                                                      session=Depends(db_session)):
                # delete_instance = query_service.model_query(
                #     filter_args=request_url_param_model.__dict__,
                #     extra_args=query.__dict__,
                #     session=session)
                filter_stmt = query_service.model_query(filter_args=request_url_param_model.__dict__,
                                                        extra_args=query.__dict__,
                                                        session=session)

                tmp = await session.execute(filter_stmt)
                delete_instance = tmp.scalar()

                return await parsing_service.async_delete_one(response_model=response_model,
                                                              sql_execute_result=delete_instance,
                                                              fastapi_response=response,
                                                              session=session)

        else:
            @api.delete(path, status_code=200, response_model=response_model, dependencies=dependencies)
            def delete_one_by_primary_key(response: Response,
                                          request: Request,
                                          query=Depends(request_query_model),
                                          request_url_param_model=Depends(request_url_model),
                                          session=Depends(db_session)):
                filter_stmt = query_service.model_query(filter_args=request_url_param_model.__dict__,
                                                        extra_args=query.__dict__,
                                                        session=session)
                delete_instance = session.execute(filter_stmt).scalar()

                return parsing_service.delete_one(response_model=response_model,
                                                  sql_execute_result=delete_instance,
                                                  fastapi_response=response,
                                                  session=session)

    @classmethod
    def delete_many(cls, api, *,
                    query_service,
                    parsing_service,
                    execute_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_query_model,
                    db_session):
        if async_mode:
            @api.delete(path, status_code=200, response_model=response_model, dependencies=dependencies)
            async def async_delete_many_by_query(response: Response,
                                                 request: Request,
                                                 query=Depends(request_query_model),
                                                 session=Depends(db_session)):
                filter_stmt = query_service.model_query(filter_args=query.__dict__,
                                                        session=session)

                tmp = await session.execute(filter_stmt)
                data_instance = [i for i in tmp.scalars()]
                return await parsing_service.async_delete_many(response_model=response_model,
                                                               sql_execute_results=data_instance,
                                                               fastapi_response=response,
                                                               session=session)
        else:

            @api.delete(path, status_code=200, response_model=response_model, dependencies=dependencies)
            def delete_many_by_query(response: Response,
                                     request: Request,
                                     query=Depends(request_query_model),
                                     session=Depends(db_session)):
                filter_stmt = query_service.model_query(filter_args=query.__dict__,
                                                        session=session)

                delete_instance = [i for i in session.execute(filter_stmt).scalars()]

                return parsing_service.delete_many(response_model=response_model,
                                                   sql_execute_results=delete_instance,
                                                   fastapi_response=response,
                                                   session=session)

    @classmethod
    def post_redirect_get(cls, api, *,
                          dependencies,
                          request_body_model,
                          db_session,
                          crud_service,
                          result_parser,
                          execute_service,
                          async_mode,
                          response_model):
        if async_mode:
            @api.post("", status_code=303, response_class=Response, dependencies=dependencies)
            async def async_create_one_and_redirect_to_get_one_api_with_primary_key(
                    request: Request,
                    insert_args: request_body_model = Depends(),
                    session=Depends(db_session),
            ):
                new_inserted_data = crud_service.insert_one(insert_args=insert_args.__dict__)

                execute_service.add(session, new_inserted_data)
                try:
                    await execute_service.async_flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return await result_parser.async_post_redirect_get(response_model=response_model,
                                                                   sql_execute_result=new_inserted_data,
                                                                   fastapi_request=request,
                                                                   session=session)
        else:
            @api.post("", status_code=303, response_class=Response, dependencies=dependencies)
            def create_one_and_redirect_to_get_one_api_with_primary_key(
                    request: Request,
                    insert_args: request_body_model = Depends(),
                    session=Depends(db_session),
            ):

                new_inserted_data = crud_service.insert_one(insert_args=insert_args.__dict__)

                execute_service.add(session, new_inserted_data)
                try:
                    execute_service.flush(session)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

                return result_parser.post_redirect_get(response_model=response_model,
                                                       sql_execute_result=new_inserted_data,
                                                       fastapi_request=request,
                                                       session=session)

    @classmethod
    def patch_one(cls, api, *,
                  path,
                  response_model,
                  dependencies,
                  request_url_param_model,
                  request_body_model,
                  request_query_model,
                  execute_service,
                  db_session,
                  crud_service,
                  result_parser,
                  async_mode):
        if async_mode:

            @api.patch(path,
                       status_code=200,
                       response_model=Union[response_model],
                       dependencies=dependencies)
            async def async_partial_update_one_by_primary_key(
                    response: Response,
                    primary_key: request_url_param_model = Depends(),
                    patch_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):
                filter_stmt = crud_service.model_query(filter_args=primary_key.__dict__,
                                                       extra_args=extra_query.__dict__,
                                                       session=session)

                data_instance = await session.execute(filter_stmt)
                data_instance = data_instance.scalar()

                try:
                    return await result_parser.async_update(response_model=response_model,
                                                            sql_execute_result=data_instance,
                                                            update_args=patch_data.__dict__,
                                                            fastapi_response=response,
                                                            session=session,
                                                            update_one=True)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
        else:
            @api.patch(path,
                       status_code=200,
                       response_model=Union[response_model],
                       dependencies=dependencies)
            def partial_update_one_by_primary_key(
                    response: Response,
                    primary_key: request_url_param_model = Depends(),
                    patch_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):
                filter_stmt = crud_service.model_query(filter_args=primary_key.__dict__,
                                                       extra_args=extra_query.__dict__,
                                                       session=session)

                update_instance = session.execute(filter_stmt).scalar()

                try:
                    return result_parser.update(response_model=response_model,
                                                sql_execute_result=update_instance,
                                                update_args=patch_data.__dict__,
                                                fastapi_response=response,
                                                session=session,
                                                update_one=True)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

    @classmethod
    def patch_many(cls, api, *,
                   path,
                   response_model,
                   dependencies,
                   request_body_model,
                   request_query_model,
                   db_session,
                   crud_service,
                   result_parser,
                   execute_service,
                   async_mode):
        if async_mode:
            @api.patch(path,
                       status_code=200,
                       response_model=response_model,
                       dependencies=dependencies)
            async def async_partial_update_many_by_query(
                    response: Response,
                    patch_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session)
            ):

                filter_stmt = crud_service.model_query(filter_args=extra_query.__dict__,
                                                       session=session)

                tmp = await session.execute(filter_stmt)
                data_instance = [i for i in tmp.scalars()]

                if not data_instance:
                    return Response(status_code=HTTPStatus.NO_CONTENT)
                try:
                    return await result_parser.async_update(response_model=response_model,
                                                            sql_execute_result=data_instance,
                                                            fastapi_response=response,
                                                            update_args=patch_data.__dict__,
                                                            session=session,
                                                            update_one=False)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
        else:
            @api.patch(path,
                       status_code=200,
                       response_model=response_model,
                       dependencies=dependencies)
            def partial_update_many_by_query(
                    response: Response,
                    patch_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session)
            ):
                filter_stmt = crud_service.model_query(filter_args=extra_query.__dict__,
                                                       session=session)

                data_instance = [i for i in session.execute(filter_stmt).scalars()]

                if not data_instance:
                    return Response(status_code=HTTPStatus.NO_CONTENT)
                try:
                    return result_parser.update(response_model=response_model,
                                                sql_execute_result=data_instance,
                                                fastapi_response=response,
                                                update_args=patch_data.__dict__,
                                                session=session,
                                                update_one=False)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

    @classmethod
    def put_one(cls, api, *,
                path,
                request_url_param_model,
                request_body_model,
                response_model,
                dependencies,
                request_query_model,
                db_session,
                crud_service,
                result_parser,
                execute_service,
                async_mode):
        if async_mode:
            @api.put(path, status_code=200, response_model=response_model, dependencies=dependencies)
            async def async_entire_update_by_primary_key(
                    response: Response,
                    primary_key: request_url_param_model = Depends(),
                    update_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):
                filter_stmt = crud_service.model_query(filter_args=primary_key.__dict__,
                                                       extra_args=extra_query.__dict__,
                                                       session=session)

                data_instance = await session.execute(filter_stmt)
                data_instance = data_instance.scalar()

                if not data_instance:
                    return Response(status_code=HTTPStatus.NOT_FOUND)
                try:
                    return await result_parser.async_update(response_model=response_model,
                                                            sql_execute_result=data_instance,
                                                            fastapi_response=response,
                                                            update_args=update_data.__dict__,
                                                            session=session,
                                                            update_one=True)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
        else:
            @api.put(path, status_code=200, response_model=response_model, dependencies=dependencies)
            def entire_update_by_primary_key(
                    response: Response,
                    primary_key: request_url_param_model = Depends(),
                    update_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):
                filter_stmt = crud_service.model_query(filter_args=primary_key.__dict__,
                                                       extra_args=extra_query.__dict__,
                                                       session=session)

                data_instance = session.execute(filter_stmt).scalar()

                if not data_instance:
                    return Response(status_code=HTTPStatus.NOT_FOUND)
                try:
                    return result_parser.update(response_model=response_model,
                                                sql_execute_result=data_instance,
                                                fastapi_response=response,
                                                update_args=update_data.__dict__,
                                                session=session,
                                                update_one=True)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

    @classmethod
    def put_many(cls, api, *,
                 path,
                 response_model,
                 dependencies,
                 request_query_model,
                 request_body_model,
                 db_session,
                 crud_service,
                 result_parser,
                 execute_service,
                 async_mode):
        if async_mode:
            @api.put(path, status_code=200, response_model=response_model, dependencies=dependencies)
            async def async_entire_update_many_by_query(
                    response: Response,
                    update_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):
                filter_stmt = crud_service.model_query(filter_args=extra_query.__dict__,
                                                       session=session)
                tmp = await session.execute(filter_stmt)
                data_instance = [i for i in tmp.scalars()]

                if not data_instance:
                    return Response(status_code=HTTPStatus.NO_CONTENT)
                try:
                    return await result_parser.async_update(response_model=response_model,
                                                            sql_execute_result=data_instance,
                                                            fastapi_response=response,
                                                            update_args=update_data.__dict__,
                                                            session=session,
                                                            update_one=False)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

        else:
            @api.put(path, status_code=200, response_model=response_model, dependencies=dependencies)
            def entire_update_many_by_query(
                    response: Response,
                    update_data: request_body_model = Depends(),
                    extra_query: request_query_model = Depends(),
                    session=Depends(db_session),
            ):

                filter_stmt = crud_service.model_query(filter_args=extra_query.__dict__,
                                                       session=session)

                data_instance = [i for i in session.execute(filter_stmt).scalars()]

                if not data_instance:
                    return Response(status_code=HTTPStatus.NO_CONTENT)
                try:
                    return result_parser.update(response_model=response_model,
                                                sql_execute_result=data_instance,
                                                fastapi_response=response,
                                                update_args=update_data.__dict__,
                                                session=session,
                                                update_one=False)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result

                # return result_parser.update_many(response_model=response_model,
                #                                  sql_execute_result=query_result,
                #                                  fastapi_response=response,
                #                                  session=session)

    @classmethod
    def find_one_foreign_tree(cls, api, *,
                              query_service,
                              parsing_service,
                              execute_service,
                              async_mode,
                              path,
                              response_model,
                              dependencies,
                              request_query_model,
                              request_url_param_model,
                              function_name,
                              db_session):

        if async_mode:
            @api.get(path, dependencies=dependencies, response_model=response_model, name=function_name)
            async def async_get_one_with_foreign_tree(response: Response,
                                                      request: Request,
                                                      url_param=Depends(request_url_param_model),
                                                      query=Depends(request_query_model),
                                                      session=Depends(
                                                          db_session)
                                                      ):
                target_model = request.url.path.split("/")[-2]
                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_one_with_foreign_pk(query=query.__dict__,
                                                             join_mode=join,
                                                             abstract_param=url_param.__dict__,
                                                             target_model=target_model)

                query_result = await execute_service.async_execute(session, stmt)

                parsed_response = await parsing_service.async_find_one(response_model=response_model,
                                                                       sql_execute_result=query_result,
                                                                       fastapi_response=response,
                                                                       join_mode=join,
                                                                       session=session)
                return parsed_response
        else:
            @api.get(path, dependencies=dependencies, response_model=response_model, name=function_name)
            def get_one_with_foreign_tree(response: Response,
                                          request: Request,
                                          url_param=Depends(request_url_param_model),
                                          query=Depends(request_query_model),
                                          session=Depends(
                                              db_session)
                                          ):
                target_model = request.url.path.split("/")[-2]
                join = query.__dict__.pop('join_foreign_table', None)

                stmt = query_service.get_one_with_foreign_pk(query=query.__dict__,
                                                             join_mode=join,
                                                             abstract_param=url_param.__dict__,
                                                             target_model=target_model)
                query_result = execute_service.execute(session, stmt)
                parsed_response = parsing_service.find_one(response_model=response_model,
                                                           sql_execute_result=query_result,
                                                           fastapi_response=response,
                                                           join_mode=join,
                                                           session=session)
                return parsed_response

    @classmethod
    def find_many_foreign_tree(cls, api, *,
                               query_service,
                               parsing_service,
                               execute_service,
                               async_mode,
                               path,
                               response_model,
                               dependencies,
                               request_query_model,
                               request_url_param_model,
                               function_name,
                               db_session):

        if async_mode:
            @api.get(path, dependencies=dependencies, response_model=response_model, name=function_name)
            async def async_get_many_with_foreign_tree(response: Response,
                                                       request: Request,
                                                       url_param=Depends(request_url_param_model),
                                                       query=Depends(request_query_model),
                                                       session=Depends(
                                                           db_session)
                                                       ):
                target_model = request.url.path.split("/")[-1]
                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_many(query=query.__dict__, join_mode=join, abstract_param=url_param.__dict__,
                                              target_model=target_model)

                query_result = await execute_service.async_execute(session, stmt)

                parsed_response = await parsing_service.async_find_many(response_model=response_model,
                                                                        sql_execute_result=query_result,
                                                                        fastapi_response=response,
                                                                        join_mode=join,
                                                                        session=session)
                return parsed_response
        else:
            @api.get(path, dependencies=dependencies, response_model=response_model, name=function_name)
            def get_many_with_foreign_tree(response: Response,
                                           request: Request,
                                           url_param=Depends(request_url_param_model),
                                           query=Depends(request_query_model),
                                           session=Depends(
                                               db_session)
                                           ):
                target_model = request.url.path.split("/")[-1]
                join = query.__dict__.pop('join_foreign_table', None)
                stmt = query_service.get_many(query=query.__dict__, join_mode=join, abstract_param=url_param.__dict__,
                                              target_model=target_model)
                query_result = execute_service.execute(session, stmt)
                parsed_response = parsing_service.find_many(response_model=response_model,
                                                            sql_execute_result=query_result,
                                                            fastapi_response=response,
                                                            join_mode=join,
                                                            session=session)

                return parsed_response


class SQLAlchemyPGSQLRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        if async_mode:

            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_one_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list)

                try:
                    query_result = await execute_service.async_execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT, content=err_msg)
                    return result
                return await parsing_service.async_upsert_one(response_model=response_model,
                                                              sql_execute_result=query_result,
                                                              fastapi_response=response,
                                                              session=session)
        else:

            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_one_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):

                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list)
                try:
                    query_result = execute_service.execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT, content=err_msg)
                    return result
                return parsing_service.upsert_one(response_model=response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):

        if async_mode:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_many_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list,
                                            upsert_one=False)
                try:
                    query_result = await execute_service.async_execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT, content=err_msg)
                    return result
                return await parsing_service.async_upsert_many(response_model=response_model,
                                                               sql_execute_result=query_result,
                                                               fastapi_response=response,
                                                               session=session)
        else:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_many_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list,
                                            upsert_one=False)
                try:
                    query_result = execute_service.execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT, content=err_msg)
                    return result
                return parsing_service.upsert_many(response_model=response_model,
                                                   sql_execute_result=query_result,
                                                   fastapi_response=response,
                                                   session=session)


class SQLAlchemySQLLiteRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        if async_mode:

            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_one_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list)

                try:
                    query_result = await execute_service.async_execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return await parsing_service.async_upsert_one(response_model=response_model,
                                                              sql_execute_result=query_result,
                                                              fastapi_response=response,
                                                              session=session)
        else:

            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_one_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):

                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list)
                try:
                    query_result = execute_service.execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return parsing_service.upsert_one(response_model=response_model,
                                                  sql_execute_result=query_result,
                                                  fastapi_response=response,
                                                  session=session)

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):

        if async_mode:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            async def async_insert_many_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):
                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list,
                                            upsert_one=False)
                try:
                    query_result = await execute_service.async_execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return await parsing_service.async_upsert_many(response_model=response_model,
                                                               sql_execute_result=query_result,
                                                               fastapi_response=response,
                                                               session=session)
        else:
            @api.post(path, status_code=201, response_model=response_model, dependencies=dependencies)
            def insert_many_and_support_upsert(
                    response: Response,
                    request: Request,
                    query: request_body_model = Depends(request_body_model),
                    session=Depends(db_session)
            ):

                stmt = query_service.upsert(insert_arg=query.__dict__,
                                            unique_fields=unique_list,
                                            upsert_one=False)
                try:
                    query_result = execute_service.execute(session, stmt)
                except IntegrityError as e:
                    err_msg, = e.orig.args
                    if 'unique constraint' not in err_msg.lower():
                        raise e
                    result = Response(status_code=HTTPStatus.CONFLICT)
                    return result
                return parsing_service.upsert_many(response_model=response_model,
                                                   sql_execute_result=query_result,
                                                   fastapi_response=response,
                                                   session=session)


class SQLAlchemyMySQLRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):
        raise NotImplementedError


class SQLAlchemyMariadbRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):
        raise NotImplementedError


class SQLAlchemyOracleRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):
        raise NotImplementedError


class SQLAlchemyMSSQLRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):
        raise NotImplementedError


class SQLAlchemyNotSupportRouteSource(SQLAlchemyGeneralSQLBaseRouteSource):
    '''
    This route will support the SQL SQLAlchemy dialects
    '''

    @classmethod
    def upsert_one(cls, api, *,
                   path,
                   query_service,
                   parsing_service,
                   execute_service,
                   async_mode,
                   response_model,
                   request_body_model,
                   dependencies,
                   db_session,
                   unique_list):
        raise NotImplementedError

    @classmethod
    def upsert_many(cls, api, *,
                    query_service,
                    parsing_service,
                    async_mode,
                    path,
                    response_model,
                    dependencies,
                    request_body_model,
                    db_session,
                    unique_list,
                    execute_service):
        raise NotImplementedError
