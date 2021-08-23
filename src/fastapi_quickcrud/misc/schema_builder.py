import uuid
import warnings
from copy import deepcopy
from dataclasses import make_dataclass, field
from typing import Optional, Any
from typing import Type, Dict, List, Tuple, TypeVar, NewType, Union

import pydantic
from fastapi import Body, Query
from pydantic import BaseModel, create_model, root_validator, BaseConfig
from pydantic.dataclasses import dataclass as pydantic_dataclass
from sqlalchemy import UniqueConstraint
from sqlalchemy import inspect, PrimaryKeyConstraint
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import declarative_base

from .exceptions import MultipleSingleUniqueNotSupportedException, \
    SchemaException, \
    CompositePrimaryKeyConstraintNotSupportedException, \
    MultiplePrimaryKeyNotSupportedException, \
    ColumnTypeNotSupportedException, \
    UnknownError
from .type import MatchingPatternInString, \
    RangeFromComparisonOperators, \
    Ordering, \
    RangeToComparisonOperators, \
    ExtraFieldTypePrefix, \
    ExtraFieldType, \
    ItemComparisonOperators

BaseModelT = TypeVar('BaseModelT', bound=BaseModel)
DataClass = NewType('DataClass', Any)
DeclarativeClass = NewType('DeclarativeClass', declarative_base)


class OrmConfig(BaseConfig):
    orm_mode = True


def _add_orm_model_config_into_pydantic_model(pydantic_model, **kwargs):
    validators = kwargs.get('validators', None)
    config = kwargs.get('config', None)
    field_definitions = {
        name_: (field_.outer_type_, field_.field_info.default)
        for name_, field_ in pydantic_model.__fields__.items()
    }
    return create_model(f'{pydantic_model.__name__}WithValidators',
                        **field_definitions,
                        __config__=config,
                        __validators__=validators)


def _add_validators(model: Type[BaseModelT], validators, **kwargs) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all optional and no default
    """

    config = kwargs.get('config', None)

    field_definitions = {
        name_: (field_.outer_type_, field_.field_info.default)
        for name_, field_ in model.__fields__.items()
    }
    return create_model(f'{model.__name__}WithValidators',
                        **field_definitions,
                        __config__=config,
                        __validators__={**validators})


def _model_from_dataclass(kls: DataClass) -> Type[BaseModel]:
    """ Converts a stdlib dataclass to a pydantic BaseModel """

    return pydantic_dataclass(kls).__pydantic_model__


def _original_data_to_alias(alias_name_dict):
    def core(_, values):
        for original_name, alias_name in alias_name_dict.items():
            if original_name in values:
                values[alias_name] = values.pop(original_name)
        return values

    return core


def _to_require_but_default(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all require but there are default value
    """
    config = model.Config
    field_definitions = {}
    for name_, field_ in model.__fields__.items():
        field_definitions[name_] = (field_.outer_type_, field_.field_info.default)
    return create_model(f'RequireButDefault{model.__name__}', **field_definitions,
                        __config__=config)  # type: ignore[arg-type]


def _filter_none(request_or_response_object):
    received_request = deepcopy(request_or_response_object.__dict__)
    if 'insert' in received_request:
        insert_item_without_null = []
        for received_insert in received_request['insert']:
            received_insert_ = deepcopy(received_insert)
            for received_insert_item, received_insert_value in received_insert_.__dict__.items():
                if hasattr(received_insert_value, '__module__'):
                    if received_insert_value.__module__ == 'fastapi.params' or received_insert_value is None:
                        delattr(received_insert, received_insert_item)
                elif received_insert_value is None:
                    delattr(received_insert, received_insert_item)

            insert_item_without_null.append(received_insert)
        setattr(request_or_response_object, 'insert', insert_item_without_null)
    else:
        for name, value in received_request.items():
            if hasattr(value, '__module__'):
                if value.__module__ == 'fastapi.params' or value is None:
                    delattr(request_or_response_object, name)
            elif value is None:
                delattr(request_or_response_object, name)


class ApiParameterSchemaBuilder:
    unsupported_data_types = ["BLOB"]
    partial_supported_data_types = ["INTERVAL", "JSON", "JSONB"]

    def __init__(self, db_model: Type, exclude_column=None):
        if exclude_column is None:
            self._exclude_column = []
        else:
            self._exclude_column = exclude_column
        self.__db_model: DeclarativeClass = db_model
        self.alias_mapper: Dict[str, str] = self._alias_mapping_builder()

        self.primary_key_str, self._primary_key_dataclass_model, self._primary_key_field_definition \
            = self._extract_primary()
        self.unique_fields: List[str] = self._extract_unique()
        self.uuid_type_columns = []
        self.str_type_columns = []
        self.number_type_columns = []
        self.datetime_type_columns = []
        self.timedelta_type_columns = []
        self.bool_type_columns = []
        self.json_type_columns = []
        self.array_type_columns = []
        self.all_field: List[dict] = self._extract_all_field()

    def _alias_mapping_builder(self) -> Dict[str, str]:
        # extract all field and check the alias_name in info and build a mapping
        # return dictionary
        #   key: original name
        #   value : alias name
        alias_mapping = {}

        mapper = inspect(self.__db_model)
        for attr in mapper.attrs:
            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    column, = attr.columns
                    if 'alias_name' in column.info:
                        name = column.info['alias_name']
                        alias_mapping[attr.key] = name
        return alias_mapping

    def _extract_unique(self) -> List[str]:
        # get the unique columns with alias name

        # service change alias to original
        #   handle:
        #       composite unique constraint
        #       single unique
        #   exception:
        #       use composite unique constraint if more than one column using unique
        #       can not use composite unique constraint and single unique at same time
        #
        unique_column_list = []
        composite_unique_constraint = []
        if hasattr(self.__db_model, '__table_args__'):
            for constraints in self.__db_model.__table_args__:
                if isinstance(constraints, UniqueConstraint):
                    for constraint in constraints:
                        column_name = constraint.key
                        if column_name in self.alias_mapper:
                            unique_column_name = self.alias_mapper[column_name]
                        else:
                            unique_column_name = column_name
                        composite_unique_constraint.append(unique_column_name)

        mapper = inspect(self.__db_model)
        for attr in mapper.attrs:
            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    column, = attr.columns
                    if column.unique:
                        column_name = attr.key
                        if column_name in self.alias_mapper:
                            unique_column_name = self.alias_mapper[column_name]
                        else:
                            unique_column_name = column_name
                        unique_column_list.append(unique_column_name)
        if unique_column_list and composite_unique_constraint:
            invalid = set(unique_column_list) - set(composite_unique_constraint)
            if invalid:
                raise SchemaException("Use single unique constraint and composite unique constraint "
                                      "at same time is not supported ")
        if len(unique_column_list) > 1 and not composite_unique_constraint:
            raise MultipleSingleUniqueNotSupportedException(
                " In case you need composite unique constraint, "
                "FastAPi CRUD builder is not support to define multiple unique=True "
                "but specifying UniqueConstraint(…) in __table_args__."
                f'''
                __table_args__ = (
                    UniqueConstraint({''.join(unique_column_list)}),
                )
                ''')

        return unique_column_list or composite_unique_constraint

    def _extract_primary(self) -> Tuple[Union[str, Any],
                                        DataClass,
                                        Tuple[Union[str, Any],
                                              Union[Type[uuid.UUID], Any],
                                              Optional[Any]]]:
        # get the primary columns with alias
        #   handle:
        #       primary key
        #   exception:
        #       composite primary key constraint not supported
        #       can not more than one primary key
        if hasattr(self.__db_model, '__table_args__'):
            for constraints in self.__db_model.__table_args__:
                if isinstance(constraints, PrimaryKeyConstraint):
                    raise CompositePrimaryKeyConstraintNotSupportedException(
                        'Primary Key Constraint not supported')
        mapper = inspect(self.__db_model)
        primary_list = self.__db_model.__table__.primary_key.columns.values()
        if len(primary_list) > 1:
            raise MultiplePrimaryKeyNotSupportedException(
                f'multiple primary key not supported; {str(mapper.mapped_table)} ')
        primary_key_column, = primary_list
        column_type = str(primary_key_column.type)
        try:
            python_type = primary_key_column.type.python_type
            if column_type in self.unsupported_data_types:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {primary_key_column.key} ({column_type}) not supported yet')
            if column_type in self.partial_supported_data_types:
                warnings.warn(
                    f'The type of column {primary_key_column.key} ({column_type}) '
                    f'is not support data query (as a query parameters )')

        except NotImplementedError:
            if column_type == "UUID":
                python_type = uuid.UUID
            else:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {primary_key_column.key} ({column_type}) not supported yet')
        # handle if python type is UUID
        if python_type.__name__ in ['str',
                                    'int',
                                    'float',
                                    'Decimal',
                                    'UUID',
                                    'bool',
                                    'date',
                                    'time',
                                    'datetime']:
            column_type = python_type
        else:
            raise ColumnTypeNotSupportedException(
                f'The type of column {primary_key_column.key} ({column_type}) not supported yet')

        default = self._extra_default_value(primary_key_column)
        if default is ...:
            warnings.warn(
                f'The column of {primary_key_column.key} has not default value '
                f'and it is not nullable but in exclude_list'
                f'it may throw error when you write data through Fast-qucikcrud greated API')
        column_name = primary_key_column.key
        if column_name in self.alias_mapper:
            primary_column_name = self.alias_mapper[column_name]
        else:
            primary_column_name = primary_key_column.key
        primary_field_definitions = (primary_column_name, column_type, default)

        primary_columns_model: DataClass = make_dataclass('PrimaryKeyModel',
                                                          [(primary_field_definitions[0],
                                                            primary_field_definitions[1],
                                                            Query(primary_field_definitions[2]))],
                                                          namespace={
                                                              '__post_init__': lambda
                                                                  self_object: self._value_of_list_to_str(
                                                                  self_object, self.uuid_type_columns)
                                                          })

        assert primary_column_name and primary_columns_model and primary_field_definitions
        return primary_column_name, primary_columns_model, primary_field_definitions

    @staticmethod
    def _value_of_list_to_str(request_or_response_object, columns):
        received_request = deepcopy(request_or_response_object.__dict__)
        if isinstance(columns, str):
            columns = [columns]
        if 'insert' in request_or_response_object.__dict__:
            insert_str_list = []
            for insert_item in request_or_response_object.__dict__['insert']:
                for column in columns:
                    for insert_item_column, _ in insert_item.__dict__.items():
                        if column in insert_item_column:
                            value_ = insert_item.__dict__[insert_item_column]
                            if value_ is not None:
                                if isinstance(value_, list):
                                    str_value_ = [str(i) for i in value_]
                                else:
                                    str_value_ = str(value_)
                                setattr(insert_item, insert_item_column, str_value_)
                insert_str_list.append(insert_item)
            setattr(request_or_response_object, 'insert', insert_str_list)
        else:
            for column in columns:
                for received_column_name, _ in received_request.items():
                    if column in received_column_name:
                        value_ = received_request[received_column_name]
                        if value_ is not None:
                            if isinstance(value_, list):
                                str_value_ = [str(i) for i in value_]
                            else:
                                str_value_ = str(value_)
                            setattr(request_or_response_object, received_column_name, str_value_)

    @staticmethod
    def _get_many_string_matching_patterns_description_builder():
        return '''<br >Composite string field matching pattern<h5/> 
                   <br /> Allow to select more than one pattern for string query
                   <br /> <a> https://www.postgresql.org/docs/9.3/functions-matching.html <a/>'''

    @staticmethod
    def _get_many_order_by_columns_description_builder(all_columns, regex_validation, primary_name):
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

    @staticmethod
    def _extra_default_value(column):
        if not column.nullable:
            if column.default is not None:
                default = column.default.arg
            elif column.server_default is not None:
                default = None
            elif column.primary_key and column.autoincrement:
                default = None
            else:
                default = ...
        else:
            if column.default is not None:
                default = column.default.arg
            else:
                default = None
        return default

    def _extract_all_field(self) -> List[dict]:
        fields: List[dict] = []
        mapper = inspect(self.__db_model)
        for attr in mapper.attrs:
            if isinstance(attr, ColumnProperty):
                if attr.columns:
                    column, = attr.columns
                    default = self._extra_default_value(column)
                    if attr.key in self._exclude_column:
                        continue
                    column_name = attr.key
                    if column_name in self.alias_mapper:
                        column_name = self.alias_mapper[column_name]

                    column_type = str(column.type)
                    try:
                        python_type = column.type.python_type
                        if column_type in self.unsupported_data_types:
                            raise ColumnTypeNotSupportedException(
                                f'The type of column {attr.key} ({column_type}) not supported yet')
                        if column_type in self.partial_supported_data_types:
                            warnings.warn(
                                f'The type of column {attr.key} ({column_type}) '
                                f'is not support data query (as a query parameters )')

                    except NotImplementedError:
                        if column_type == "UUID":
                            python_type = uuid.UUID
                        else:
                            raise ColumnTypeNotSupportedException(
                                f'The type of column {attr.key} ({column_type}) not supported yet')

                    # string filter
                    if python_type.__name__ in ['str']:
                        self.str_type_columns.append(column_name)
                    # uuid filter
                    elif python_type.__name__ in ['UUID']:
                        self.uuid_type_columns.append(column_name)
                    # number filter
                    elif python_type.__name__ in ['int', 'float', 'Decimal']:
                        self.number_type_columns.append(column_name)
                    # date filter
                    elif python_type.__name__ in ['date', 'time', 'datetime']:
                        self.datetime_type_columns.append(column_name)
                    # timedelta filter
                    elif python_type.__name__ in ['timedelta']:
                        self.timedelta_type_columns.append(column_name)
                    # bool filter
                    elif python_type.__name__ in ['bool']:
                        self.bool_type_columns.append(column_name)
                    # json filter
                    elif python_type.__name__ in ['dict']:
                        self.json_type_columns.append(column_name)
                    # array filter
                    elif python_type.__name__ in ['list']:
                        self.array_type_columns.append(column_name)
                        base_column_detail, = column.base_columns
                        if hasattr(base_column_detail.type, 'item_type'):
                            item_type = base_column_detail.type.item_type.python_type
                            fields.append({'column_name': column_name,
                                           'column_type': List[item_type],
                                           'column_default': default})
                            continue
                    else:
                        raise ColumnTypeNotSupportedException(
                            f'The type of column {attr.key} ({column_type}) not supported yet')

                    if column_type == "JSONB":
                        fields.append({'column_name': column_name,
                                       'column_type': Union[python_type, list],
                                       'column_default': default})
                    else:
                        fields.append({'column_name': column_name,
                                       'column_type': python_type,
                                       'column_default': default})
        return fields

    @staticmethod
    def _assign_str_matching_pattern(field_of_param: dict, result_: List[dict]) -> List[dict]:
        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str + ExtraFieldType.Matching_pattern,
             'column_type': Optional[List[MatchingPatternInString]],
             'column_default': [MatchingPatternInString.case_sensitive]},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None}
        ]:
            result_.append(i)
        return result_

    @staticmethod
    def _assign_list_comparison(field_of_param, result_: List[dict]) -> List[dict]:
        for i in [
            {
                'column_name': field_of_param[
                                   'column_name'] + f'{ExtraFieldTypePrefix.List}{ExtraFieldType.Comparison_operator}',
                'column_type': Optional[ItemComparisonOperators],
                'column_default': ItemComparisonOperators.In},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.List,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None}

        ]:
            result_.append(i)
        return result_

    @staticmethod
    def _assign_range_comparison(field_of_param, result_: List[dict]) -> List[dict]:
        for i in [
            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.From}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeFromComparisonOperators],
             'column_default': RangeFromComparisonOperators.Greater_than_or_equal_to},

            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.To}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeToComparisonOperators],
             'column_default': RangeToComparisonOperators.Less_than.Less_than_or_equal_to},
        ]:
            result_.append(i)

        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.From,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.From, field_of_param['column_type'])],
             'column_default': None},

            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.To,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.To, field_of_param['column_type'])],

             'column_default': None}
        ]:
            result_.append(i)
        return result_

    def _get_fizzy_query_param(self, exclude_column: List[str] = None) -> List[dict]:
        if not exclude_column:
            exclude_column = []
        fields_: List[dict] = deepcopy(self.all_field)
        result = []
        for field_ in fields_:
            if field_['column_name'] in exclude_column:
                continue
            field_['column_default'] = None
            if field_['column_name'] in self.str_type_columns:
                result = self._assign_str_matching_pattern(field_, result)
                result = self._assign_list_comparison(field_, result)

            elif field_['column_name'] in self.uuid_type_columns or \
                    field_['column_name'] in self.bool_type_columns:
                result = self._assign_list_comparison(field_, result)

            elif field_['column_name'] in self.number_type_columns or \
                    field_['column_name'] in self.datetime_type_columns:
                result = self._assign_range_comparison(field_, result)
                result = self._assign_list_comparison(field_, result)

        return result

    def _assign_pagination_param(self, result_: List[tuple]) -> List[tuple]:
        all_column_ = [i['column_name'] for i in self.all_field]

        regex_validation = "(?=(" + '|'.join(all_column_) + r")?\s?:?\s*?(?=(" + '|'.join(
            list(map(str, Ordering))) + r"))?)"
        columns_with_ordering = pydantic.constr(regex=regex_validation)
        for i in [
            ('limit', Optional[int], Query(None)),
            ('offset', Optional[int], Query(None)),
            ('order_by_columns', Optional[List[columns_with_ordering]], Query(
                # [f"{self._primary_key}:ASC"],
                None,
                description=self._get_many_order_by_columns_description_builder(
                    all_columns=all_column_,
                    regex_validation=regex_validation,
                    primary_name=self.primary_key_str)))
        ]:
            result_.append(i)
        return result_

    def upsert_one(self) -> Tuple:
        request_validation = [lambda self_object: _filter_none(self_object)]
        request_fields = []
        response_fields = []

        # Create on_conflict Model
        all_column_ = [i['column_name'] for i in self.all_field]
        conflict_columns = ('update_columns',
                            Optional[List[str]],
                            Body(set(all_column_) - set(self.unique_fields),
                                 description='update_columns should contain which columns you want to update '
                                             'when the unique columns got conflict'))
        conflict_model = make_dataclass('Upsert_one_request_update_columns_when_conflict_request_body_model',
                                        [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Body(i['column_default'])))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass('Upsert_one_request_model',
                                            request_fields + on_conflict_handle,
                                            namespace={
                                                '__post_init__': lambda self_object: [i(self_object)
                                                                                      for i in request_validation]
                                            })

        response_model_dataclass = make_dataclass('Upsert_one_response_model',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model = _to_require_but_default(response_model_pydantic)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})
        else:
            response_model = _add_orm_model_config_into_pydantic_model(response_model)
        return None, request_body_model, response_model

    def upsert_many(self) -> Tuple:
        insert_fields = []
        response_fields = []

        # Create on_conflict Model
        all_column_ = [i['column_name'] for i in self.all_field]
        conflict_columns = ('update_columns',
                            Optional[List[str]],
                            Body(set(all_column_) - set(self.unique_fields),
                                 description='update_columns should contain which columns you want to update '
                                             f'when the unique columns got conflict'))
        conflict_model = make_dataclass('Upsert_many_request_update_columns_when_conflict_request_body_model',
                                        [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Ready the Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            insert_fields.append((i['column_name'],
                                  i['column_type'],
                                  field(default=Body(i['column_default']))))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        #
        # # Ready uuid_to_str validator
        # if self.uuid_type_columns:
        #     for uuid_name in self.uuid_type_columns:
        #         validator_function = validator(uuid_name, allow_reuse=True)(_uuid_to_str)
        #         request_validator_dict[f'{uuid_name}_validator'] = validator_function
        #
        # # Add filter out none field validator and uuid_to_str validaor
        # request_validator_dict['root_validator'] = root_validator(allow_reuse=True)(
        #     _filter_out_none)  # <- should be check none has filted and uuid is str
        #
        # insert_item_field = make_dataclass('UpsertManyInsertItemRequestModel',
        #                                    insert_fields
        #                                    )
        # insert_item_field_model_pydantic = _model_from_dataclass(insert_item_field)
        # insert_item_field_model_pydantic = _add_validators(insert_item_field_model_pydantic, request_validator_dict)
        request_validation = [lambda self_object: _filter_none(self_object)]

        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))

        insert_item_field_model_pydantic = make_dataclass('UpsertManyInsertItemRequestModel',
                                                          insert_fields
                                                          )

        # Create List Model with contains item
        insert_list_field = [('insert', List[insert_item_field_model_pydantic], Body(...))]
        request_body_model = make_dataclass('UpsertManyRequestBody',
                                            insert_list_field + on_conflict_handle
                                            ,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]}
                                            )

        response_model_dataclass = make_dataclass('UpsertManyResponseItemModel',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_item_model = _to_require_but_default(response_model_pydantic)
        if self.alias_mapper and response_item_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_item_model = _add_validators(response_item_model, {"root_validator": validator_function})

        response_model = create_model(
            'UpsertManyResponseListModel',
            **{'__root__': (List[response_item_model], None)}
        )

        return None, request_body_model, response_model

    def find_many(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param()
        query_param: List[dict] = self._assign_pagination_param(query_param)

        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    None))
            # i['column_type']))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('FindManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]}
                                             )
        response_model_dataclass = make_dataclass('FindManyResponseItemModel',
                                                  response_fields,
                                                  )
        response_list_item_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_list_item_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_list_item_model = _add_validators(response_list_item_model, {"root_validator": validator_function},
                                                       config=OrmConfig)
        else:

            response_list_item_model = _add_orm_model_config_into_pydantic_model(response_list_item_model,
                                                                                 config=OrmConfig)

        response_model = create_model(
            'FindManyResponseListModel',
            **{'__root__': (List[response_list_item_model], None), '__config__': OrmConfig}
        )

        return request_query_model, None, response_model

    def find_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('FindOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model_dataclass = make_dataclass('FindOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function}, config=OrmConfig)
        else:
            response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
        return self._primary_key_dataclass_model, request_query_model, None, response_model

    def delete_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)
        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass('DeleteOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model = make_dataclass('DeleteOneResponseModel',
                                        [(self._primary_key_field_definition[0],
                                          self._primary_key_field_definition[1],
                                          ...)],
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)
        response_model = _add_orm_model_config_into_pydantic_model(response_model)
        return self._primary_key_dataclass_model, request_query_model, None, response_model

    def delete_many(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param()
        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass('DeleteManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model = make_dataclass('DeleteManyResponseModel',
                                        [(self._primary_key_field_definition[0],
                                          self._primary_key_field_definition[1],
                                          ...)],
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)

        response_model = create_model(
            'DeleteManyResponseListModel',
            **{'__root__': (List[response_model], None)}
        )

        return None, request_query_model, None, response_model

    def patch(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] is not self.primary_key_str:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(None)))

        request_query_fields = []
        for i in query_param:
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('PatchOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('PatchOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('PatchOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return self._primary_key_dataclass_model, request_query_model, request_body_model, response_model

    def update_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] is not self.primary_key_str:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(...)))

        request_query_fields = []
        for i in query_param:
            # if isinstance(i, Tuple):
            #     request_query_fields.append(i)
            #     request_body_fields.append()
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('UpdateOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('UpdateOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('UpdateOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return self._primary_key_dataclass_model, request_query_model, request_body_model, response_model

    def update_many(self) -> Tuple:
        """
        In update many, it allow you update some columns into the same value in limit of a scope,
        you can get the limit of scope by using request query.
        And fill out the columns (except the primary key column and unique columns) you want to update
        and the update value in the request body

        The response will show you the update result
        :return: url param dataclass model
        """
        query_param: List[dict] = self._get_fizzy_query_param()

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] not in [self.primary_key_str]:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(...)))

        request_query_fields = []
        for i in query_param:
            # if isinstance(i, Tuple):
            #     request_query_fields.append(i)
            #     request_body_fields.append()
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('UpdateManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('UpdateManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('UpdateManyResponseModel',
                                                  response_fields,
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model_dataclass:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model_pydantic = _add_validators(response_model_pydantic, {"root_validator": validator_function})

        response_model = create_model(
            'UpdateManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )

        return None, request_query_model, request_body_model, response_model

    def patch_many(self) -> Tuple:
        """
        In update many, it allow you update some columns into the same value in limit of a scope,
        you can get the limit of scope by using request query.
        And fill out the columns (except the primary key column and unique columns) you want to update
        and the update value in the request body

        The response will show you the update result
        :return: url param dataclass model
        """
        query_param: List[dict] = self._get_fizzy_query_param()

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] not in [self.primary_key_str]:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(None)))

        request_query_fields = []
        for i in query_param:
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('PatchManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('PatchManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('PatchManyResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model_dataclass:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model_pydantic = _add_validators(response_model_pydantic, {"root_validator": validator_function})

        response_model = create_model(
            'PatchManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )

        return None, request_query_model, request_body_model, response_model

    def post_redirect_get(self) -> Tuple:
        request_validation = [lambda self_object: _filter_none(self_object)]
        request_body_fields = []
        response_body_fields = []

        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_body_fields.append((i['column_name'],
                                        i['column_type'],
                                        Body(i['column_default'])))
            response_body_fields.append((i['column_name'],
                                         i['column_type'],
                                         Body(i['column_default'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass('PostAndRedirectRequestModel',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator(self_object)
                                                                                      for validator in
                                                                                      request_validation]
                                            })

        response_model_dataclass = make_dataclass('PostAndRedirectResponseModel',
                                                  response_body_fields)
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return None, request_body_model, response_model


class ApiParameterSchemaBuilderForTable:
    unsupported_data_types = ["BLOB"]
    partial_supported_data_types = ["INTERVAL", "JSON", "JSONB"]

    def __init__(self, db_model: Type, exclude_column=None):
        if exclude_column is None:
            self._exclude_column = []
        else:
            self._exclude_column = exclude_column
        self.__db_model: DeclarativeClass = db_model
        self.__columns = db_model.c

        self.alias_mapper: Dict[str, str] = {}  # Table not support alias

        self.primary_key_str, self._primary_key_dataclass_model, self._primary_key_field_definition \
            = self._extract_primary()
        self.unique_fields: List[str] = self._extract_unique()
        self.uuid_type_columns = []
        self.str_type_columns = []
        self.number_type_columns = []
        self.datetime_type_columns = []
        self.timedelta_type_columns = []
        self.bool_type_columns = []
        self.json_type_columns = []
        self.array_type_columns = []
        self.all_field: List[dict] = self._extract_all_field()

    def _alias_mapping_builder(self) -> Dict[str, str]:
        # extract all field and check the alias_name in info and build a mapping
        # return dictionary
        #   key: original name
        #   value : alias name
        alias_mapping = {}
        for column in self.__columns:
            info: dict = column.info
            if 'alias_name' in info:
                name = column.info['alias_name']
                alias_mapping[column.key] = name
        return alias_mapping

    def _extract_unique(self) -> List[str]:
        # get the unique columns with alias name

        # service change alias to original
        #   handle:
        #       composite unique constraint
        #       single unique
        #   exception:
        #       use composite unique constraint if more than one column using unique
        #       can not use composite unique constraint and single unique at same time
        #
        unique_constraint = None
        constraints = self.__db_model.constraints
        for constraint in constraints:
            if isinstance(constraint, UniqueConstraint):
                if unique_constraint:
                    raise SchemaException(
                        "Only support one unique constraint/ Use unique constraint and composite unique constraint "
                        "at same time is not supported / Use  composite unique constraint if there are more than one unique constraint")
                unique_constraint = constraint
        if unique_constraint:
            unique_column_name_list = []
            for constraint_column in unique_constraint.columns:
                column_name = str(constraint_column.key)
                if column_name in self.alias_mapper:
                    unique_column_name = self.alias_mapper[column_name]
                else:
                    unique_column_name = column_name
                unique_column_name_list.append(unique_column_name)
            return unique_column_name_list
        else:
            return []

    def _extract_primary(self) -> Union[tuple, Tuple[Union[str, Any],
                                                     DataClass,
                                                     Tuple[Union[str, Any],
                                                           Union[Type[uuid.UUID], Any],
                                                           Optional[Any]]]]:

        primary_list = self.__db_model.primary_key.columns.values()
        if not primary_list:
            return (None, None, None)
        if len(primary_list) > 1:
            raise MultiplePrimaryKeyNotSupportedException(
                f'multiple primary key not supported; {str(self.__db_model.name)} ')
        primary_key_column, = primary_list
        column_type = str(primary_key_column.type)
        try:
            python_type = primary_key_column.type.python_type
            if column_type in self.unsupported_data_types:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {primary_key_column.key} ({column_type}) not supported yet')
            if column_type in self.partial_supported_data_types:
                warnings.warn(
                    f'The type of column {primary_key_column.key} ({column_type}) '
                    f'is not support data query (as a query parameters )')

        except NotImplementedError:
            if column_type == "UUID":
                python_type = uuid.UUID
            else:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {primary_key_column.key} ({column_type}) not supported yet')
        # handle if python type is UUID
        if python_type.__name__ in ['str',
                                    'int',
                                    'float',
                                    'Decimal',
                                    'UUID',
                                    'bool',
                                    'date',
                                    'time',
                                    'datetime']:
            column_type = python_type
        else:
            raise ColumnTypeNotSupportedException(
                f'The type of column {primary_key_column.key} ({column_type}) not supported yet')

        default = self._extra_default_value(primary_key_column)
        if default is ...:
            warnings.warn(
                f'The column of {primary_key_column.key} has not default value '
                f'and it is not nullable but in exclude_list'
                f'it may throw error when you write data through Fast-qucikcrud greated API')
        primary_column_name = str(primary_key_column.key)
        primary_field_definitions = (primary_column_name, column_type, default)

        primary_columns_model: DataClass = make_dataclass('PrimaryKeyModel',
                                                          [(primary_field_definitions[0],
                                                            primary_field_definitions[1],
                                                            Query(primary_field_definitions[2]))],
                                                          namespace={
                                                              '__post_init__': lambda
                                                                  self_object: self._value_of_list_to_str(
                                                                  self_object, self.uuid_type_columns)
                                                          })

        assert primary_column_name and primary_columns_model and primary_field_definitions
        return primary_column_name, primary_columns_model, primary_field_definitions

    @staticmethod
    def _value_of_list_to_str(request_or_response_object, columns):
        received_request = deepcopy(request_or_response_object.__dict__)
        if isinstance(columns, str):
            columns = [columns]
        if 'insert' in request_or_response_object.__dict__:
            insert_str_list = []
            for insert_item in request_or_response_object.__dict__['insert']:
                for column in columns:
                    for insert_item_column, _ in insert_item.__dict__.items():
                        if column in insert_item_column:
                            value_ = insert_item.__dict__[insert_item_column]
                            if value_ is not None:
                                if isinstance(value_, list):
                                    str_value_ = [str(i) for i in value_]
                                else:
                                    str_value_ = str(value_)
                                setattr(insert_item, insert_item_column, str_value_)
                insert_str_list.append(insert_item)
            setattr(request_or_response_object, 'insert', insert_str_list)
        else:
            for column in columns:
                for received_column_name, _ in received_request.items():
                    if column in received_column_name:
                        value_ = received_request[received_column_name]
                        if value_ is not None:
                            if isinstance(value_, list):
                                str_value_ = [str(i) for i in value_]
                            else:
                                str_value_ = str(value_)
                            setattr(request_or_response_object, received_column_name, str_value_)

    @staticmethod
    def _get_many_string_matching_patterns_description_builder():
        return '''<br >Composite string field matching pattern<h5/> 
                   <br /> Allow to select more than one pattern for string query
                   <br /> <a> https://www.postgresql.org/docs/9.3/functions-matching.html <a/>'''

    @staticmethod
    def _get_many_order_by_columns_description_builder(all_columns, regex_validation, primary_name):
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

    @staticmethod
    def _extra_default_value(column):
        if not column.nullable:
            if column.default is not None:
                default = column.default.arg
            elif column.server_default is not None:
                default = None
            elif column.primary_key and column.autoincrement:
                default = None
            else:
                default = ...
        else:
            if column.default is not None:
                default = column.default.arg
            else:
                default = None
        return default

    def _extract_all_field(self) -> List[dict]:
        fields: List[dict] = []

        for column in self.__columns:
            column_name = str(column.key)
            default = self._extra_default_value(column)
            if column_name in self._exclude_column:
                continue
            column_type = str(column.type)
            try:
                python_type = column.type.python_type
                if column_type in self.unsupported_data_types:
                    raise ColumnTypeNotSupportedException(
                        f'The type of column {column_name} ({column_type}) not supported yet')
                if column_type in self.partial_supported_data_types:
                    warnings.warn(
                        f'The type of column {column_name} ({column_type}) '
                        f'is not support data query (as a query parameters )')

            except NotImplementedError:
                if column_type == "UUID":
                    python_type = uuid.UUID
                else:
                    raise ColumnTypeNotSupportedException(
                        f'The type of column {column_name} ({column_type}) not supported yet')
                    # string filter
            if python_type.__name__ in ['str']:
                self.str_type_columns.append(column_name)
            # uuid filter
            elif python_type.__name__ in ['UUID']:
                self.uuid_type_columns.append(column_name)
            # number filter
            elif python_type.__name__ in ['int', 'float', 'Decimal']:
                self.number_type_columns.append(column_name)
            # date filter
            elif python_type.__name__ in ['date', 'time', 'datetime']:
                self.datetime_type_columns.append(column_name)
            # timedelta filter
            elif python_type.__name__ in ['timedelta']:
                self.timedelta_type_columns.append(column_name)
            # bool filter
            elif python_type.__name__ in ['bool']:
                self.bool_type_columns.append(column_name)
            # json filter
            elif python_type.__name__ in ['dict']:
                self.json_type_columns.append(column_name)
            # array filter
            elif python_type.__name__ in ['list']:
                self.array_type_columns.append(column_name)
                base_column_detail, = column.base_columns
                if hasattr(base_column_detail.type, 'item_type'):
                    item_type = base_column_detail.type.item_type.python_type
                    fields.append({'column_name': column_name,
                                   'column_type': List[item_type],
                                   'column_default': default})
                    continue
            else:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {column_name} ({column_type}) not supported yet')

            if column_type == "JSONB":
                fields.append({'column_name': column_name,
                               'column_type': Union[python_type, list],
                               'column_default': default})
            else:
                fields.append({'column_name': column_name,
                               'column_type': python_type,
                               'column_default': default})

        return fields

    @staticmethod
    def _assign_str_matching_pattern(field_of_param: dict, result_: List[dict]) -> List[dict]:
        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str + ExtraFieldType.Matching_pattern,
             'column_type': Optional[List[MatchingPatternInString]],
             'column_default': [MatchingPatternInString.case_sensitive]},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None}
        ]:
            result_.append(i)
        return result_

    @staticmethod
    def _assign_list_comparison(field_of_param, result_: List[dict]) -> List[dict]:
        for i in [
            {
                'column_name': field_of_param[
                                   'column_name'] + f'{ExtraFieldTypePrefix.List}{ExtraFieldType.Comparison_operator}',
                'column_type': Optional[ItemComparisonOperators],
                'column_default': ItemComparisonOperators.In},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.List,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None}

        ]:
            result_.append(i)
        return result_

    @staticmethod
    def _assign_range_comparison(field_of_param, result_: List[dict]) -> List[dict]:
        for i in [
            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.From}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeFromComparisonOperators],
             'column_default': RangeFromComparisonOperators.Greater_than_or_equal_to},

            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.To}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeToComparisonOperators],
             'column_default': RangeToComparisonOperators.Less_than.Less_than_or_equal_to},
        ]:
            result_.append(i)

        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.From,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.From, field_of_param['column_type'])],
             'column_default': None},

            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.To,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.To, field_of_param['column_type'])],

             'column_default': None}
        ]:
            result_.append(i)
        return result_

    def _get_fizzy_query_param(self, exclude_column: List[str] = None) -> List[dict]:
        if not exclude_column:
            exclude_column = []
        fields_: List[dict] = deepcopy(self.all_field)
        result = []
        for field_ in fields_:
            if field_['column_name'] in exclude_column:
                continue
            field_['column_default'] = None
            if field_['column_name'] in self.str_type_columns:
                result = self._assign_str_matching_pattern(field_, result)
                result = self._assign_list_comparison(field_, result)

            elif field_['column_name'] in self.uuid_type_columns or \
                    field_['column_name'] in self.bool_type_columns:
                result = self._assign_list_comparison(field_, result)

            elif field_['column_name'] in self.number_type_columns or \
                    field_['column_name'] in self.datetime_type_columns:
                result = self._assign_range_comparison(field_, result)
                result = self._assign_list_comparison(field_, result)

        return result

    def _assign_pagination_param(self, result_: List[tuple]) -> List[tuple]:
        all_column_ = [i['column_name'] for i in self.all_field]

        regex_validation = "(?=(" + '|'.join(all_column_) + r")?\s?:?\s*?(?=(" + '|'.join(
            list(map(str, Ordering))) + r"))?)"
        columns_with_ordering = pydantic.constr(regex=regex_validation)
        for i in [
            ('limit', Optional[int], Query(None)),
            ('offset', Optional[int], Query(None)),
            ('order_by_columns', Optional[List[columns_with_ordering]], Query(
                # [f"{self._primary_key}:ASC"],
                None,
                description=self._get_many_order_by_columns_description_builder(
                    all_columns=all_column_,
                    regex_validation=regex_validation,
                    primary_name=self.primary_key_str)))
        ]:
            result_.append(i)
        return result_

    def upsert_one(self) -> Tuple:
        request_validation = [lambda self_object: _filter_none(self_object)]
        request_fields = []
        response_fields = []

        # Create on_conflict Model
        all_column_ = [i['column_name'] for i in self.all_field]
        conflict_columns = ('update_columns',
                            Optional[List[str]],
                            Body(set(all_column_) - set(self.unique_fields),
                                 description='update_columns should contain which columns you want to update '
                                             'when the unique columns got conflict'))
        conflict_model = make_dataclass('Upsert_one_request_update_columns_when_conflict_request_body_model',
                                        [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Body(i['column_default'])))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass('Upsert_one_request_model',
                                            request_fields + on_conflict_handle,
                                            namespace={
                                                '__post_init__': lambda self_object: [i(self_object)
                                                                                      for i in request_validation]
                                            })

        response_model_dataclass = make_dataclass('Upsert_one_response_model',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model = _to_require_but_default(response_model_pydantic)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})
        else:
            response_model = _add_orm_model_config_into_pydantic_model(response_model)
        return None, request_body_model, response_model

    def upsert_many(self) -> Tuple:
        insert_fields = []
        response_fields = []

        # Create on_conflict Model
        all_column_ = [i['column_name'] for i in self.all_field]
        conflict_columns = ('update_columns',
                            Optional[List[str]],
                            Body(set(all_column_) - set(self.unique_fields),
                                 description='update_columns should contain which columns you want to update '
                                             f'when the unique columns got conflict'))
        conflict_model = make_dataclass('Upsert_many_request_update_columns_when_conflict_request_body_model',
                                        [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Ready the Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            insert_fields.append((i['column_name'],
                                  i['column_type'],
                                  field(default=Body(i['column_default']))))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        #
        # # Ready uuid_to_str validator
        # if self.uuid_type_columns:
        #     for uuid_name in self.uuid_type_columns:
        #         validator_function = validator(uuid_name, allow_reuse=True)(_uuid_to_str)
        #         request_validator_dict[f'{uuid_name}_validator'] = validator_function
        #
        # # Add filter out none field validator and uuid_to_str validaor
        # request_validator_dict['root_validator'] = root_validator(allow_reuse=True)(
        #     _filter_out_none)  # <- should be check none has filted and uuid is str
        #
        # insert_item_field = make_dataclass('UpsertManyInsertItemRequestModel',
        #                                    insert_fields
        #                                    )
        # insert_item_field_model_pydantic = _model_from_dataclass(insert_item_field)
        # insert_item_field_model_pydantic = _add_validators(insert_item_field_model_pydantic, request_validator_dict)
        request_validation = [lambda self_object: _filter_none(self_object)]

        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))

        insert_item_field_model_pydantic = make_dataclass('UpsertManyInsertItemRequestModel',
                                                          insert_fields
                                                          )

        # Create List Model with contains item
        insert_list_field = [('insert', List[insert_item_field_model_pydantic], Body(...))]
        request_body_model = make_dataclass('UpsertManyRequestBody',
                                            insert_list_field + on_conflict_handle
                                            ,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]}
                                            )

        response_model_dataclass = make_dataclass('UpsertManyResponseItemModel',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_item_model = _to_require_but_default(response_model_pydantic)
        if self.alias_mapper and response_item_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_item_model = _add_validators(response_item_model, {"root_validator": validator_function})

        response_model = create_model(
            'UpsertManyResponseListModel',
            **{'__root__': (List[response_item_model], None)}
        )

        return None, request_body_model, response_model

    def find_many(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param()
        query_param: List[dict] = self._assign_pagination_param(query_param)

        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    None))
            # i['column_type']))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('FindManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]}
                                             )
        response_model_dataclass = make_dataclass('FindManyResponseItemModel',
                                                  response_fields,
                                                  )
        response_list_item_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_list_item_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_list_item_model = _add_validators(response_list_item_model, {"root_validator": validator_function},
                                                       config=OrmConfig)
        else:

            response_list_item_model = _add_orm_model_config_into_pydantic_model(response_list_item_model,
                                                                                 config=OrmConfig)

        response_model = create_model(
            'FindManyResponseListModel',
            **{'__root__': (List[response_list_item_model], None), '__config__': OrmConfig}
        )

        return request_query_model, None, response_model

    def find_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('FindOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model_dataclass = make_dataclass('FindOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function}, config=OrmConfig)
        else:
            response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
        return self._primary_key_dataclass_model, request_query_model, None, response_model

    def delete_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)
        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass('DeleteOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model = make_dataclass('DeleteOneResponseModel',
                                        response_fields,
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)
        response_model = _add_orm_model_config_into_pydantic_model(response_model)
        return self._primary_key_dataclass_model, request_query_model, None, response_model

    def delete_many(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param()
        response_fields = []
        all_field = deepcopy(self.all_field)
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            if isinstance(i, Tuple):
                request_fields.append(i)
            elif isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass('DeleteManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model = make_dataclass('DeleteManyResponseModel',
                                        response_fields,
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)

        response_model = create_model(
            'DeleteManyResponseListModel',
            **{'__root__': (List[response_model], None)}
        )

        return None, request_query_model, None, response_model

    def patch(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] != self.primary_key_str:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(None)))

        request_query_fields = []
        for i in query_param:
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('PatchOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('PatchOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('PatchOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return self._primary_key_dataclass_model, request_query_model, request_body_model, response_model

    def update_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            a = i['column_name']
            b = self.primary_key_str
            if i['column_name'] != self.primary_key_str:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(...)))

        request_query_fields = []
        for i in query_param:
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('UpdateOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('UpdateOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('UpdateOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return self._primary_key_dataclass_model, request_query_model, request_body_model, response_model

    def update_many(self) -> Tuple:
        """
        In update many, it allow you update some columns into the same value in limit of a scope,
        you can get the limit of scope by using request query.
        And fill out the columns (except the primary key column and unique columns) you want to update
        and the update value in the request body

        The response will show you the update result
        :return: url param dataclass model
        """
        query_param: List[dict] = self._get_fizzy_query_param()

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] not in [self.primary_key_str]:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(...)))

        request_query_fields = []
        for i in query_param:
            # if isinstance(i, Tuple):
            #     request_query_fields.append(i)
            #     request_body_fields.append()
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('UpdateManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('UpdateManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('UpdateManyResponseModel',
                                                  response_fields,
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model_dataclass:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model_pydantic = _add_validators(response_model_pydantic, {"root_validator": validator_function})

        response_model = create_model(
            'UpdateManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )

        return None, request_query_model, request_body_model, response_model

    def patch_many(self) -> Tuple:
        """
        In update many, it allow you update some columns into the same value in limit of a scope,
        you can get the limit of scope by using request query.
        And fill out the columns (except the primary key column and unique columns) you want to update
        and the update value in the request body

        The response will show you the update result
        :return: url param dataclass model
        """
        query_param: List[dict] = self._get_fizzy_query_param()

        response_fields = []
        all_field = deepcopy(self.all_field)
        request_body_fields = []

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))
            if i['column_name'] not in [self.primary_key_str]:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(None)))

        request_query_fields = []
        for i in query_param:
            if isinstance(i, dict):
                request_query_fields.append((i['column_name'],
                                             i['column_type'],
                                             Query(i['column_default'])))
            else:
                raise UnknownError(f'Unknown error, {i}')

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass('PatchManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass('PatchManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass('PatchManyResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model_dataclass:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model_pydantic = _add_validators(response_model_pydantic, {"root_validator": validator_function})

        response_model = create_model(
            'PatchManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )

        return None, request_query_model, request_body_model, response_model

    def post_redirect_get(self) -> Tuple:
        request_validation = [lambda self_object: _filter_none(self_object)]
        request_body_fields = []
        response_body_fields = []

        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_body_fields.append((i['column_name'],
                                        i['column_type'],
                                        Body(i['column_default'])))
            response_body_fields.append((i['column_name'],
                                         i['column_type'],
                                         Body(i['column_default'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass('PostAndRedirectRequestModel',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator(self_object)
                                                                                      for validator in
                                                                                      request_validation]
                                            })

        response_model_dataclass = make_dataclass('PostAndRedirectResponseModel',
                                                  response_body_fields)
        response_model = _model_from_dataclass(response_model_dataclass)
        if self.alias_mapper and response_model:
            validator_function = root_validator(pre=True, allow_reuse=True)(_original_data_to_alias(self.alias_mapper))
            response_model = _add_validators(response_model, {"root_validator": validator_function})

        return None, request_body_model, response_model
