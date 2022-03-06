from itertools import groupby
from typing import Type, List, Union, TypeVar, Optional

from pydantic import BaseModel, BaseConfig
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.elements import \
    or_, \
    BinaryExpression

from sqlalchemy.sql.schema import Table

from .covert_model import convert_table_to_model
from .crud_model import RequestResponseModel, CRUDModel
from .exceptions import QueryOperatorNotFound, PrimaryMissing, UnknownColumn
from .schema_builder import ApiParameterSchemaBuilder
from .type import \
    CrudMethods, \
    CRUDRequestMapping, \
    MatchingPatternInStringBase, \
    ExtraFieldType, \
    RangeFromComparisonOperators, \
    ExtraFieldTypePrefix, \
    RangeToComparisonOperators, \
    ItemComparisonOperators, PGSQLMatchingPatternInString, SqlType, FOREIGN_PATH_PARAM_KEYWORD

Base = TypeVar("Base", bound=declarative_base)

BaseModelT = TypeVar('BaseModelT', bound=BaseModel)

__all__ = [
    'sqlalchemy_to_pydantic',
    # 'sqlalchemy_table_to_pydantic',
    'find_query_builder',
    'Base',
    'clean_input_fields',
    'group_find_many_join',
    'convert_table_to_model']

unsupported_data_types = ["BLOB"]
partial_supported_data_types = ["INTERVAL", "JSON", "JSONB"]


def clean_input_fields(param: Union[dict, list], model: Base):
    assert isinstance(param, dict) or isinstance(param, list) or isinstance(param, set)

    if isinstance(param, dict):
        stmt = {}
        for column_name, value in param.items():
            if column_name == '__initialised__':
                continue
            column = getattr(model, column_name)
            actual_column_name = column.expression.key
            stmt[actual_column_name] = value
        return stmt
    if isinstance(param, list) or isinstance(param, set):
        stmt = []
        for column_name in param:
            if not hasattr(model, column_name):
                raise UnknownColumn(f'column {column_name} is not exited')
            column = getattr(model, column_name)
            actual_column_name = column.expression.key
            stmt.append(actual_column_name)
        return stmt


def find_query_builder(param: dict, model: Base) -> List[Union[BinaryExpression]]:
    query = []
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


class OrmConfig(BaseConfig):
    orm_mode = True


def sqlalchemy_to_pydantic(
        db_model: Type, *,
        crud_methods: List[CrudMethods],
        sql_type: str = SqlType.postgresql,
        exclude_columns: List[str] = None,
        constraints=None,
        foreign_include: Optional[any] = None,
        exclude_primary_key=False) -> CRUDModel:
    db_model, _ = convert_table_to_model(db_model)
    if exclude_columns is None:
        exclude_columns = []
    if foreign_include is None:
        foreign_include = {}
    request_response_mode_set = {}
    model_builder = ApiParameterSchemaBuilder(db_model,
                                              constraints=constraints,
                                              exclude_column=exclude_columns,
                                              sql_type=sql_type,
                                              foreign_include=foreign_include,
                                              exclude_primary_key=exclude_primary_key)

    REQUIRE_PRIMARY_KEY_CRUD_METHOD = [CrudMethods.DELETE_ONE.value,
                                       CrudMethods.FIND_ONE.value,
                                       CrudMethods.PATCH_ONE.value,
                                       CrudMethods.POST_REDIRECT_GET.value,
                                       CrudMethods.UPDATE_ONE.value]
    for crud_method in crud_methods:
        request_url_param_model = None
        request_body_model = None
        response_model = None
        request_query_model = None
        foreignListModel = None
        if crud_method.value in REQUIRE_PRIMARY_KEY_CRUD_METHOD and not model_builder.primary_key_str:
            raise PrimaryMissing(f"The generation of this API [{crud_method.value}] requires a primary key")

        if crud_method.value == CrudMethods.UPSERT_ONE.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.upsert_one()
        elif crud_method.value == CrudMethods.UPSERT_MANY.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.upsert_many()
        elif crud_method.value == CrudMethods.CREATE_ONE.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.create_one()
        elif crud_method.value == CrudMethods.CREATE_MANY.value:
            request_query_model, \
            request_body_model, \
            response_model = model_builder.create_many()
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
            response_model, \
            relationship_list = model_builder.find_one()
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
        elif crud_method.value == CrudMethods.FIND_ONE_WITH_FOREIGN_TREE.value:
            foreignListModel = model_builder.foreign_tree_get_one()
        elif crud_method.value == CrudMethods.FIND_MANY_WITH_FOREIGN_TREE.value:
            foreignListModel = model_builder.foreign_tree_get_many()

        request_response_models = {'requestBodyModel': request_body_model,
                                   'responseModel': response_model,
                                   'requestQueryModel': request_query_model,
                                   'requestUrlParamModel': request_url_param_model,
                                   'foreignListModel': foreignListModel}
        request_response_model = RequestResponseModel(**request_response_models)
        request_method = CRUDRequestMapping.get_request_method_by_crud_method(crud_method.value).value
        if request_method not in request_response_mode_set:
            request_response_mode_set[request_method] = {}
        request_response_mode_set[request_method][crud_method.value] = request_response_model
    return CRUDModel(
        **{**request_response_mode_set,
           **{"PRIMARY_KEY_NAME": model_builder.primary_key_str,
              "UNIQUE_LIST": model_builder.unique_fields}})


# def get_many_string_matching_patterns_description_builder() -> str:
#     return '''<br >Composite string field matching pattern<h5/>
#            <br /> Allow to select more than one pattern for string query'''


# def get_many_order_by_columns_description_builder(*, all_columns, regex_validation, primary_name) -> str:
#     return f'''<br> support column:
#     <br> {all_columns} <hr><br> support ordering:
#     <br> {list(map(str, Ordering))}
#     <hr>
#     <br> field input validation regex
#     <br> {regex_validation}
#     <hr>
#     <br />example:
#     <br />&emsp;&emsp;{primary_name}:ASC
#     <br />&emsp;&emsp;{primary_name}: DESC
#     <br />&emsp;&emsp;{primary_name}    :    DESC
#     <br />&emsp;&emsp;{primary_name} (default sort by ASC)'''


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

    MatchingPatternInStringBase.case_insensitive:
        lambda field, values: or_(field.ilike(value) for value in values),

    MatchingPatternInStringBase.case_sensitive:
        lambda field, values: or_(field.like(value) for value in values),

    MatchingPatternInStringBase.not_case_insensitive:
        lambda field, values: or_(field.not_ilike(value) for value in values),

    MatchingPatternInStringBase.not_case_sensitive:
        lambda field, values: or_(field.not_like(value) for value in values),

    MatchingPatternInStringBase.contains:
        lambda field, values: or_(field.contains(value) for value in values),

    PGSQLMatchingPatternInString.similar_to:
        lambda field, values: or_(field.op("SIMILAR TO")(value) for value in values),

    PGSQLMatchingPatternInString.not_similar_to:
        lambda field, values: or_(field.op("NOT SIMILAR TO")(value) for value in values),

    PGSQLMatchingPatternInString.match_regex_with_case_sensitive:
        lambda field, values: or_(field.op("~")(value) for value in values),

    PGSQLMatchingPatternInString.match_regex_with_case_insensitive:
        lambda field, values: or_(field.op("~*")(value) for value in values),

    PGSQLMatchingPatternInString.does_not_match_regex_with_case_sensitive:
        lambda field, values: or_(field.op("!~")(value) for value in values),

    PGSQLMatchingPatternInString.does_not_match_regex_with_case_insensitive:
        lambda field, values: or_(field.op("!~*")(value) for value in values)
}


def table_to_declarative_base(db_model):
    db_name = str(db_model.fullname)
    Base = declarative_base()
    if not db_model.primary_key:
        db_model.append_column(Column('__id', Integer, primary_key=True, autoincrement=True))
    table_dict = {'__tablename__': db_name}
    for i in db_model.c:
        _, = i.expression.base_columns
        _.table = None
        table_dict[str(i.key)] = _
    tmp = type(f'{db_name}', (Base,), table_dict)
    tmp.__table__ = db_model
    return tmp


def group_find_many_join(list_of_dict: List[dict]) -> List[dict]:
    def group_by_foreign_key(item):
        tmp = {}
        for k, v in item.items():
            if '_foreign' not in k:
                tmp[k] = v
        return tmp

    response_list = []
    for key, group in groupby(list_of_dict, group_by_foreign_key):
        response = {}
        for i in group:
            for k, v in i.items():
                if '_foreign' in k:
                    if k not in response:
                        response[k] = [v]
                    else:
                        response[k].append(v)
            for response_ in response:
                i.pop(response_, None)
            result = {**i, **response}
        response_list.append(result)
    return response_list


def path_query_builder(params, model) -> List[Union[BinaryExpression]]:
    query = []
    if not params:
        return query
    for param_name, param_value in params.items():
        table_with_column = param_name.split(FOREIGN_PATH_PARAM_KEYWORD)
        assert len(table_with_column) == 2
        table_name, column_name = table_with_column
        table_model = model[table_name]
        query.append((getattr(table_model, column_name) == param_value))
    return query
