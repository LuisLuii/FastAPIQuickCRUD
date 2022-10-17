from typing import \
    List, \
    TypeVar, Union, Optional

from fastapi import \
    APIRouter
from pydantic import \
    BaseModel
from sqlalchemy.sql.schema import Table

from . import sqlalchemy_to_pydantic
from .generator.common_module_template_generator import CommonModuleTemplateGenerator
from .generator.crud_template_generator import CrudTemplateGenerator
from .misc.crud_model import CRUDModel
from .misc.get_table_name import get_table_name
from .misc.type import CrudMethods, SqlType
from .misc.utils import convert_table_to_model
from .model.common_builder import CommonCodeGen
from .model.crud_builder import CrudCodeGen

CRUDModelType = TypeVar("CRUDModelType", bound=BaseModel)
CompulsoryQueryModelType = TypeVar("CompulsoryQueryModelType", bound=BaseModel)
OnConflictModelType = TypeVar("OnConflictModelType", bound=BaseModel)


def crud_router_builder(
        *,
        db_model_list: Union[Table, 'DeclarativeBaseModel'],
        async_mode: Optional[bool],
        sql_type: Optional[SqlType],
        crud_methods: Optional[List[CrudMethods]] = None,
        exclude_columns: Optional[List[str]] = None,
        # foreign_include: Optional[Base] = None
) -> APIRouter:
    """
    @param db_model:
        The Sqlalchemy Base model/Table you want to use it to build api.

    @param async_mode:
        As your database connection

    @param sql_type:
        You sql database type

    @param db_session:
        The callable variable and return a session generator that will be used to get database connection session for fastapi.

    @param crud_methods:
        Fastapi Quick CRUD supports a few of crud methods, and they save into the Enum class,
        get it by : from fastapi_quickcrud_codegen_codegen import CrudMethods
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

    @param foreign_include: BaseModel
        Used to build foreign tree api

    @return:
        APIRouter for fastapi
    """
    model_list = []
    for db_model_info in db_model_list:

        db_model = db_model_info["db_model"]
        prefix = db_model_info["prefix"]
        tags = db_model_info["tags"]

        table_name = db_model.__name__
        model_name = get_table_name(db_model)

        model_list.append({"model_name": model_name, "file_name": table_name})


        db_model, NO_PRIMARY_KEY = convert_table_to_model(db_model)

        # code gen
        crud_code_generator = CrudCodeGen(model_name, model_name=table_name, tags=tags, prefix=prefix)
        # create a file
        crud_template_generator = CrudTemplateGenerator()

        constraints = db_model.__table__.constraints

        common_module_template_generator = CommonModuleTemplateGenerator()

        # type
        common_code_builder = CommonCodeGen()
        common_code_builder.build_type()
        common_code_builder.gen(common_module_template_generator.add_type)

        # module
        common_utils_code_builder = CommonCodeGen()
        common_utils_code_builder.build_utils()
        common_utils_code_builder.gen(common_module_template_generator.add_utils)

        # http_exception
        common_http_exception_code_builder = CommonCodeGen()
        common_http_exception_code_builder.build_http_exception()
        common_http_exception_code_builder.gen(common_module_template_generator.add_http_exception)

        # db
        common_db_code_builder = CommonCodeGen()
        common_db_code_builder.build_db()
        common_db_code_builder.gen(common_module_template_generator.add_db)

        if not crud_methods and NO_PRIMARY_KEY == False:
            crud_methods = CrudMethods.get_declarative_model_full_crud_method()
        if not crud_methods and NO_PRIMARY_KEY == True:
            crud_methods = CrudMethods.get_table_full_crud_method()

        crud_models_builder: CRUDModel = sqlalchemy_to_pydantic
        crud_models: CRUDModel = crud_models_builder(db_model=db_model,
                                                     constraints=constraints,
                                                     crud_methods=crud_methods,
                                                     exclude_columns=exclude_columns,
                                                     sql_type=sql_type,
                                                     exclude_primary_key=NO_PRIMARY_KEY)

        methods_dependencies = crud_models.get_available_request_method()
        primary_name = crud_models.PRIMARY_KEY_NAME
        if primary_name:
            path = '/{' + primary_name + '}'
        else:
            path = ""

        def find_one_api():
            crud_code_generator.build_find_one_route(async_mode=async_mode, path=path)

        api_register = {
            CrudMethods.FIND_ONE.value: find_one_api,
        }
        for request_method in methods_dependencies:
            value_of_dict_crud_model = crud_models.get_model_by_request_method(request_method)
            crud_model_of_this_request_methods = value_of_dict_crud_model.keys()
            for crud_model_of_this_request_method in crud_model_of_this_request_methods:
                api_register[crud_model_of_this_request_method.value]()
        crud_code_generator.gen(crud_template_generator)

    # sql session
    common_db_session_code_builder = CommonCodeGen()
    common_db_session_code_builder.build_db_session(model_list=model_list)
    common_db_session_code_builder.gen(common_module_template_generator.add_memory_sql_session)

    # app py
    common_app_code_builder = CommonCodeGen()
    common_app_code_builder.build_app(model_list=model_list)
    common_app_code_builder.gen(common_module_template_generator.add_app)
