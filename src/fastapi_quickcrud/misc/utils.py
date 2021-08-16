import datetime
import decimal
import re
import uuid
from functools import singledispatch
from typing import Type, List, Union, TypeVar, Dict

from fastapi import FastAPI, APIRouter
from fastapi_quickcrud.misc.crud_model import RequestResponseModel, CRUDModel
from pydantic import BaseModel, create_model, BaseConfig
from sqlalchemy import any_, text, Integer
from sqlalchemy.sql.elements import \
    or_, \
    and_, BinaryExpression

from .exceptions import QueryOperatorNotFound
from .schema_builder import ApiParameterSchemaBuilder
from .type import \
    Base, \
    CrudMethods, \
    CRUDRequestMapping, \
    MatchingPatternInString, \
    Ordering, \
    ExtraFieldType, \
    RangeFromComparisonOperators, \
    ExtraFieldTypePrefix, \
    RangeToComparisonOperators, \
    ItemComparisonOperators

BaseModelT = TypeVar('BaseModelT', bound=BaseModel)

__all__ = [
    'sqlalchemy_to_pydantic',
    'filter_none_from_dict',
    'strict_query_builder',
    'find_query_builder',
    'to_require_but_default',
    'to_optional',
    'to_optional_null',
    'Base',
    'alias_to_column',
    'get_many_order_by_columns_description_builder',
    'get_many_string_matching_patterns_description_builder']

unsupported_data_types = ["BLOB"]
partial_supported_data_types = ["INTERVAL", "JSON", "JSONB"]


def filter_none_from_dict_factory(data):
    return dict(x for x in data if x[1] is not None)


def uuid_to_str(value, values):
    if value is not None:
        return str(value)


def original_data_to_alias(alias_name_dict):
    def core(_, values):
        for original_name, alias_name in alias_name_dict.items():
            if original_name in values:
                values[alias_name] = values.pop(original_name)
        return values

    return core


def add_validators(model: Type[BaseModelT], validators) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all optional and no default
    """
    config = model.Config
    field_definitions = {
        name: (field.outer_type_, field.field_info.default)
        for name, field in model.__fields__.items()
    }
    return create_model(f'{model.__name__}_validators_added',
                        **field_definitions,
                        __config__=config,
                        __validators__={**validators})


def to_optional_null(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all optional and no keep the default value
    """
    config = model.Config
    field_definitions = {
        name: (field.outer_type_, None)
        for name, field in model.__fields__.items()
    }
    return create_model(f'Optional{model.__name__}', **field_definitions, __config__=config)


def to_optional(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all optional and keep the default value
    """
    config = model.Config

    field_definitions = {}
    for name, field in model.__fields__.items():
        field_definitions[name] = (field.outer_type_, field.default if field.default else None)
    return create_model(f'Optional{model.__name__}', **field_definitions, __config__=config)  # t


def to_require_but_default(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all require but there are default value
    """
    config = model.Config
    field_definitions = {}
    for name, field in model.__fields__.items():
        field_definitions[name] = (field.outer_type_, field.field_info.default)
    return create_model(f'Required{model.__name__}', **field_definitions,
                        __config__=config)  # type: ignore[arg-type]


def to_require(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all require but there are default value
    """
    config = model.Config
    field_definitions = {}
    for name, field in model.__fields__.items():
        field_definitions[name] = (field.outer_type_, ...)
    return create_model(f'Required{model.__name__}', **field_definitions,
                        __config__=config)  # type: ignore[arg-type]



def alias_to_column(param: Union[dict, list], model: Base, column_collection: bool = False):
    assert isinstance(param, dict) or isinstance(param, list) or isinstance(param, set)

    if isinstance(param, dict):
        stmt = {}
        for column_name, value in param.items():
            if not hasattr(model, column_name):
                continue
            alias_name = getattr(model, column_name)
            if column_collection:
                actual_column_name = getattr(model, alias_name.expression.key)
            else:
                actual_column_name = alias_name.expression.key
            stmt[actual_column_name] = value
        return stmt
    if isinstance(param, list) or isinstance(param, set):
        stmt = []
        for column_name in param:
            alias_name = getattr(model, column_name)
            if column_collection:
                actual_column_name = getattr(model, alias_name.expression.key)
            else:
                actual_column_name = alias_name.expression.key
            stmt.append(actual_column_name)
        return stmt


def find_query_builder(param: dict, model: Base) -> List[Union[BinaryExpression]]:
    query = []
    '''
    columns, process_data_type, process_type
    {
        columns: {
            process_data_type: 
        }
    }
    '''
    for column_name, value in param.items():
        if ExtraFieldType.Comparison_operator in column_name or ExtraFieldType.Matching_pattern in column_name:
            continue
        if ExtraFieldTypePrefix.List in column_name:
            type_ = ExtraFieldTypePrefix.List
        elif ExtraFieldTypePrefix.From in column_name:
            type_ = ExtraFieldTypePrefix.From
        elif ExtraFieldTypePrefix.To in column_name:
            type_ = ExtraFieldTypePrefix.To
        elif ExtraFieldTypePrefix.Str in column_name:
            type_ = ExtraFieldTypePrefix.Str
        else:
            query.append((getattr(model, column_name) == value))
            # raise Exception('known error')
            continue
        sub_query = []
        table_column_name = column_name.replace(type_, "")
        operator_column_name = column_name + process_type_map[type_]
        operators = param.get(operator_column_name, None)
        if not operators:
            raise QueryOperatorNotFound(f'The query operator of {column_name} not found!')
        if not isinstance(operators, list):
            operators = [operators]
        for operator in operators:
            sub_query.append(process_map[operator](getattr(model, table_column_name), value))
        query.append((or_(*sub_query)))
    return query


def strict_query_builder(param: dict, model: Base):
    query = []
    date_range_query = []
    for column_name, value in param.items():
        if '____' in column_name:
            date_range_filter_column = getattr(model, column_name.split('__')[0])
            if '____from' in column_name:
                date_range_query.append(date_range_filter_column >= value)
                continue
            if '____to' in column_name:
                date_range_query.append(date_range_filter_column <= value)
                continue

        query.append(_create_strict_query(value, getattr(model, column_name)))
    if date_range_query:
        query.append(and_(*date_range_query))
    return query


def filter_none_from_dict(value: dict) -> dict:
    return dict(filter(lambda item: item[1] is not None, value.items()))


class OrmConfig(BaseConfig):
    orm_mode = True


def alias(constraint_list: List['str'], fields: Dict[str, tuple], alias_name_dict: Dict[str, str]):
    for original_name, alias_name in alias_name_dict.items():
        if original_name in constraint_list:
            constraint_list.remove(original_name)
            constraint_list.append(alias_name)
        if original_name in fields:
            tmp = fields[original_name]
            fields[alias_name] = tmp
    return constraint_list, fields


def sqlalchemy_to_pydantic(
        db_model: Type, *, crud_methods: List[CrudMethods], exclude_columns: List[str] = None) -> CRUDModel:
    if exclude_columns is None:
        exclude_columns = []
    request_response_mode_set = {}
    model_builder = ApiParameterSchemaBuilder(db_model,
                                              exclude_column=exclude_columns)
    for crud_method in crud_methods:
        request_url_param_model = None
        request_body_model = None
        response_model = None
        request_query_model = None

        if crud_method.value == CrudMethods.UPSERT_ONE.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.upsert_one()
        elif crud_method.value == CrudMethods.UPSERT_MANY.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.upsert_many()
        elif crud_method.value == CrudMethods.DELETE_ONE.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.delete_one()
        elif crud_method.value == CrudMethods.DELETE_MANY.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.delete_many()
        elif crud_method.value == CrudMethods.FIND_ONE.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.find_one()
        elif crud_method.value == CrudMethods.FIND_MANY.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.find_many()
        elif crud_method.value == CrudMethods.POST_REDIRECT_GET.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.post_redirect_get()
        elif crud_method.value == CrudMethods.PATCH_ONE.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.patch()
        elif crud_method.value == CrudMethods.UPDATE_ONE.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.update_one()
        elif crud_method.value == CrudMethods.UPDATE_MANY.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.update_many()
        elif crud_method.value == CrudMethods.PATCH_MANY.value:
            request_url_param_model, \
            request_query_model, \
            request_body_model, \
            response_model = model_builder.patch_many()

        request_response_models = {'requestBodyModel': request_body_model,
                                   'responseModel': response_model,
                                   'requestQueryModel': request_query_model,
                                   'requestUrlParamModel': request_url_param_model}
        request_response_model = RequestResponseModel(**request_response_models)
        request_method = CRUDRequestMapping.get_request_method_by_crud_method(crud_method.value).value
        if request_method not in request_response_mode_set:
            request_response_mode_set[request_method] = {}
        request_response_mode_set[request_method][crud_method.value] = request_response_model
    return CRUDModel(
        **{**request_response_mode_set,
           **{"PRIMARY_KEY_NAME": model_builder.primary_key_str,
              "UNIQUE_LIST": model_builder.unique_fields}})


def add_routers(app: FastAPI, routers: List[APIRouter], **kwargs):
    for router in routers:
        app.include_router(router, **kwargs)


def find_duplicate_error(error_msg) -> str:
    regex_result = re.findall('(duplicate.*?)\nDETAIL:(.*?)\n', error_msg)
    if regex_result:
        regex_result, = regex_result
    if not len(regex_result) == 2:
        return None
    return f'{regex_result[0]}: {regex_result[1]}'


def get_many_string_matching_patterns_description_builder() -> str:
    return '''<br >Composite string field matching pattern<h5/> 
           <br /> Allow to select more than one pattern for string query'''


def get_many_order_by_columns_description_builder(*, all_columns, regex_validation, primary_name) -> str:
    return f'''<br> support column: 
    <br> {all_columns} <hr><br> support ordering:  
    <br> {list(map(str, Ordering))} 
    <hr> 
    <br> field input validation regex
    <br> {regex_validation}
    <hr> 
    <br />example: 
    <br />&emsp;&emsp;{primary_name}:ASC
    <br />&emsp;&emsp;{primary_name}: DESC 
    <br />&emsp;&emsp;{primary_name}    :    DESC
    <br />&emsp;&emsp;{primary_name} (default sort by ASC)'''


process_type_map = {
    ExtraFieldTypePrefix.List: ExtraFieldType.Comparison_operator,
    ExtraFieldTypePrefix.From: ExtraFieldType.Comparison_operator,
    ExtraFieldTypePrefix.To: ExtraFieldType.Comparison_operator,
    ExtraFieldTypePrefix.Str: ExtraFieldType.Matching_pattern,
}


process_map = {
    RangeFromComparisonOperators.Greater_than:
        lambda field, value: field > value,

    RangeFromComparisonOperators.Greater_than_or_equal_to:
        lambda field, value: field >= value,

    RangeToComparisonOperators.Less_than:
        lambda field, value: field < value,

    RangeToComparisonOperators.Less_than_or_equal_to:
        lambda field, value: field <= value,

    ItemComparisonOperators.Equal:
        lambda field, values: or_(field == value for value in values),

    ItemComparisonOperators.Not_equal:
        lambda field, values: or_(field != value for value in values),

    ItemComparisonOperators.In:
        lambda field, values: or_(field.in_(values)),

    ItemComparisonOperators.Not_in:
        lambda field, values: or_(field.notin_(values)),

    MatchingPatternInString.match_regex_with_case_sensitive:
        lambda field, values: or_(field.op("~")(value) for value in values),

    MatchingPatternInString.match_regex_with_case_insensitive:
        lambda field, values: or_(field.op("~*")(value) for value in values),

    MatchingPatternInString.does_not_match_regex_with_case_sensitive:
        lambda field, values: or_(field.op("!~")(value) for value in values),

    MatchingPatternInString.does_not_match_regex_with_case_insensitive:
        lambda field, values: or_(field.op("!~*")(value) for value in values),

    MatchingPatternInString.case_insensitive:
        lambda field, values: or_(field.ilike(value) for value in values),

    MatchingPatternInString.case_sensitive:
        lambda field, values: or_(field.like(value) for value in values),

    MatchingPatternInString.not_case_insensitive:
        lambda field, values: or_(field.not_ilike(value) for value in values),

    MatchingPatternInString.not_case_sensitive:
        lambda field, values: or_(field.not_like(value) for value in values),

    MatchingPatternInString.similar_to:
        lambda field, values: or_(field.op("SIMILAR TO")(value) for value in values),

    MatchingPatternInString.not_similar_to:
        lambda field, values: or_(field.op("NOT SIMILAR TO")(value) for value in values),
}
