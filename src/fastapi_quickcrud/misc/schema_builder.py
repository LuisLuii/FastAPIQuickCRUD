import uuid
import warnings
from copy import deepcopy
from dataclasses import (make_dataclass,
                         field)
from enum import auto
from typing import (Optional,
                    Any)
from typing import (Type,
                    Dict,
                    List,
                    Tuple,
                    TypeVar,
                    NewType,
                    Union)

import pydantic
from fastapi import (Body,
                     Query)
from pydantic import (BaseModel,
                      create_model,
                      BaseConfig)
from pydantic.dataclasses import dataclass as pydantic_dataclass
from sqlalchemy import UniqueConstraint, Table, Column
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.orm import declarative_base
from strenum import StrEnum

from .covert_model import convert_table_to_model
from .exceptions import (SchemaException,
                         ColumnTypeNotSupportedException)
from .type import (MatchingPatternInStringBase,
                   RangeFromComparisonOperators,
                   Ordering,
                   RangeToComparisonOperators,
                   ExtraFieldTypePrefix,
                   ExtraFieldType,
                   ItemComparisonOperators, PGSQLMatchingPatternInString, SqlType, )

FOREIGN_PATH_PARAM_KEYWORD = "__pk__"
BaseModelT = TypeVar('BaseModelT', bound=BaseModel)
DataClassT = TypeVar('DataClassT', bound=Any)
DeclarativeClassT = NewType('DeclarativeClassT', declarative_base)
TableNameT = NewType('TableNameT', str)
ResponseModelT = NewType('ResponseModelT', BaseModel)
ForeignKeyName = NewType('ForeignKeyName', str)
TableInstance = NewType('TableInstance', Table)


class ExcludeUnsetBaseModel(BaseModel):
    def dict(self, *args, **kwargs):
        if kwargs and kwargs.get("exclude_none") is not None:
            kwargs["exclude_unset"] = True
            return BaseModel.dict(self, *args, **kwargs)


class OrmConfig(BaseConfig):
    orm_mode = True


def _add_orm_model_config_into_pydantic_model(pydantic_model, **kwargs) -> BaseModelT:
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


# def _add_validators(model: Type[BaseModelT], validators, **kwargs) -> Type[BaseModelT]:
#     """
#     Create a new BaseModel with the exact same fields as `model`
#     but making them all optional and no default
#     """
#
#     config = kwargs.get('config', None)
#
#     field_definitions = {
#         name_: (field_.outer_type_, field_.field_info.default)
#         for name_, field_ in model.__fields__.items()
#     }
#     return create_model(f'{model.__name__}WithValidators',
#                         **field_definitions,
#                         __config__=config,
#                         __validators__={**validators})

def _model_from_dataclass(kls: DataClassT) -> Type[BaseModel]:
    """ Converts a stdlib dataclass to a pydantic BaseModel. """

    return pydantic_dataclass(kls).__pydantic_model__


def _to_require_but_default(model: Type[BaseModelT]) -> Type[BaseModelT]:
    """
    Create a new BaseModel with the exact same fields as `model`
    but making them all require but there are default value
    """
    config = model.Config
    field_definitions = {}
    for name_, field_ in model.__fields__.items():
        field_definitions[name_] = (field_.outer_type_, field_.field_info.default)
    return create_model(f'{model.__name__}RequireButDefault', **field_definitions,
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

    def __init__(self, db_model: Type, sql_type, exclude_column=None, constraints=None, exclude_primary_key=False,
                 foreign_include=False):
        self.constraints = constraints
        self.exclude_primary_key = exclude_primary_key
        if exclude_column is None:
            self._exclude_column = []
        else:
            self._exclude_column = exclude_column
        self.alias_mapper: Dict[str, str] = {}  # Table not support alias
        if self.exclude_primary_key:
            self.__db_model: Table = db_model
            self.__db_model_table: Table = db_model.__table__
            self.__columns = db_model.__table__.c
            self.db_name: str = db_model.__tablename__
        else:
            self.__db_model: DeclarativeClassT = db_model
            self.__db_model_table: Table = db_model.__table__
            self.db_name: str = db_model.__tablename__
            self.__columns = db_model.__table__.c
        model = self.__db_model
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
        self.foreign_table_response_model_sets: Dict[TableNameT, ResponseModelT] = {}
        self.all_field: List[dict] = self._extract_all_field()
        self.sql_type = sql_type

        if not foreign_include:
            foreign_include = []
        self.foreign_include = foreign_include
        self.foreign_mapper = self.__foreign_mapper_builder()
        self.relation_level = self._extra_relation_level()
        self.table_of_foreign, self.reference_mapper = self.extra_foreign_table()

    def __foreign_mapper_builder(self):
        foreign_mapper = {}
        if self.exclude_primary_key:
            return foreign_mapper
        for db_model in self.foreign_include:
            db_model, NO_PRIMARY_KEY = convert_table_to_model(db_model)
            tmp = {}
            table_name = self.__get_table_name(db_model)
            tmp["model"] = db_model
            foreign_mapper[table_name] = db_model
            tmp["db_model"] = db_model
            tmp["db_model_table"] = db_model.__table__
            tmp["db_name"] = db_model.__tablename__
            tmp["columns"] = db_model.__table__.c
            tmp["all_fields"] = self._extract_all_field(tmp["columns"])
            tmp["primary_key"] = self._extract_primary(tmp["db_model_table"])
            foreign_mapper[table_name] = tmp
        return foreign_mapper

    def __get_table_name_from_table(self, table):
        return table.name

    def __get_table_name_from_model(self, table):
        return table.__tablename__

    def __get_table_name(self, table):
        if isinstance(table, Table):
            return self.__get_table_name_from_table(table)
        else:
            return self.__get_table_name_from_model(table)

    def extra_foreign_table(self, db_model=None) -> Dict[ForeignKeyName, dict]:
        if db_model is None:
            db_model = self.__db_model
        if self.exclude_primary_key:
            return self._extra_foreign_table_from_table()
        else:
            return self._extra_foreign_table_from_declarative_base(db_model)

    def _extract_primary(self, db_model_table=None) -> Union[tuple, Tuple[Union[str, Any],
                                                                          DataClassT,
                                                                          Tuple[Union[str, Any],
                                                                                Union[Type[uuid.UUID], Any],
                                                                                Optional[Any]]]]:
        if db_model_table == None:
            db_model_table = self.__db_model_table
        primary_list = db_model_table.primary_key.columns.values()
        if not primary_list or self.exclude_primary_key:
            return (None, None, None)
        if len(primary_list) > 1:
            raise SchemaException(
                f'multiple primary key / or composite not supported; {self.db_name} ')
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
        description = self._get_field_description(primary_key_column)
        if default is ...:
            warnings.warn(
                f'The column of {primary_key_column.key} has not default value '
                f'and it is not nullable and in exclude_list'
                f'it may throw error when you insert data ')
        primary_column_name = str(primary_key_column.key)
        primary_field_definitions = (primary_column_name, column_type, default)

        primary_columns_model: DataClassT = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PrimaryKeyModel',
                                                           [(primary_field_definitions[0],
                                                             primary_field_definitions[1],
                                                             Query(primary_field_definitions[2],
                                                                   description=description))],
                                                           namespace={
                                                               '__post_init__': lambda
                                                                   self_object: self._value_of_list_to_str(
                                                                   self_object, self.uuid_type_columns)
                                                           })

        assert primary_column_name and primary_columns_model and primary_field_definitions
        return primary_column_name, primary_columns_model, primary_field_definitions

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
        if not self.constraints:
            return []
        for constraint in self.constraints:
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
                unique_column_name = column_name
                unique_column_name_list.append(unique_column_name)
            return unique_column_name_list
        else:
            return []

    @staticmethod
    def _get_field_description(column: Column) -> str:
        if not hasattr(column, 'comment'):
            return ""
        return column.comment

    def _extract_all_field(self, columns=None) -> List[dict]:
        fields: List[dict] = []
        if not columns:
            columns = self.__columns
        elif isinstance(columns, DeclarativeMeta):
            columns = columns.__table__.c
        elif isinstance(columns, Table):
            columns = columns.c
        for column in columns:
            column_name = str(column.key)
            column_foreign = [i.target_fullname for i in column.foreign_keys]
            default = self._extra_default_value(column)
            if column_name in self._exclude_column:
                continue
            column_type = str(column.type)
            description = self._get_field_description(column)
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
                                   'column_default': default,
                                   'column_description': description})
                    continue
            else:
                raise ColumnTypeNotSupportedException(
                    f'The type of column {column_name} ({column_type}) not supported yet')

            if column_type == "JSONB":
                fields.append({'column_name': column_name,
                               'column_type': Union[python_type, list],
                               'column_default': default,
                               'column_description': description,
                               'column_foreign': column_foreign})
            else:
                fields.append({'column_name': column_name,
                               'column_type': python_type,
                               'column_default': default,
                               'column_description': description,
                               'column_foreign': column_foreign})

        return fields

    def _extra_foreign_table_from_table(self) -> Dict[str, Table]:
        foreign_key_table = {}
        reference_mapper = {}
        for column in self.__columns:
            if column.foreign_keys:
                foreign_column, = column.foreign_keys
                foreign_table = foreign_column.column.table
                all_fields_ = self._extract_all_field(foreign_table.c)
                foreign_table_name = str(foreign_table.__str__())
                local = str(foreign_column.parent).split('.')
                reference = foreign_column.target_fullname.split('.')

                class BaseClass(object):
                    def __init__(self):
                        pass

                TableClass = type(f'{foreign_table_name}', (BaseClass,), {})
                # table_class = mapper(TableClass, foreign_table)

                local_reference_pairs = [{'local': {"local_table": local[0],
                                                    "local_column": local[1]},
                                          "reference": {"reference_table": reference[0],
                                                        "reference_column": reference[1]},
                                          'reference_table': foreign_table,
                                          'reference_table_columns': foreign_table.c,
                                          'local_table': foreign_column.parent.table,
                                          'local_table_columns': foreign_column.parent.table.c}]

                reference_mapper[local[1]] = {"foreign_table": foreign_table_name,
                                              "foreign_table_name": foreign_table_name}
                # foreign_key_table[foreign_table_name] = foreign_table
                # all_column = {}
                column_label = {}
                for i in foreign_table.c:
                    column_name = str(i).split('.')[1]
                    setattr(TableClass, column_name, i)
                    column_label[column_name] = i

                foreign_key_table[foreign_table_name] = {'local_reference_pairs_set': local_reference_pairs,
                                                         'fields': all_fields_,
                                                         'instance': foreign_table,
                                                         'db_column': TableClass,
                                                         'column_label': column_label}

                response_fields = []
                for i in all_fields_:
                    response_fields.append((i['column_name'],
                                            i['column_type'],
                                            None))
                response_model_dataclass = make_dataclass(
                    f'foreign_{foreign_table_name + str(uuid.uuid4())}_FindManyResponseItemModel',
                    response_fields,
                )
                response_item_model = _model_from_dataclass(response_model_dataclass)

                response_item_model = _add_orm_model_config_into_pydantic_model(response_item_model,
                                                                                config=OrmConfig)
                # response_item_model = _add_validators(response_item_model,
                #                                            config=OrmConfig)
                response_model = create_model(
                    f'foreign_{foreign_table_name + str(uuid.uuid4())}_UpsertManyResponseListModel',
                    **{'__root__': (List[response_item_model], None)}
                )

                self.foreign_table_response_model_sets[foreign_table_name] = response_model
                foreign_key_table[foreign_table_name] = {'local_reference_pairs_set': local_reference_pairs,
                                                         'fields': all_fields_,
                                                         'instance': foreign_table,
                                                         'db_column': foreign_table}

        return foreign_key_table, reference_mapper

    def _extra_relation_level(self, model=None, processed_table=None) -> Dict[str, Table]:
        if model is None:
            model = self.__db_model
        if not processed_table:
            processed_table = []
        mapper = inspect(model)
        relation_level = []
        for r in mapper.relationships:

            target_table = r.target
            target_model, _ = convert_table_to_model(target_table)
            target_table_name = target_model.__tablename__
            if target_table_name and target_table_name not in processed_table and target_table_name in self.foreign_mapper:
                processed_table.append(str(mapper.local_table))
                if self.foreign_mapper[target_table_name]["db_name"] not in relation_level:
                    relation_level.append(self.foreign_mapper[target_table_name]["db_name"])
                relation_level += self._extra_relation_level(self.foreign_mapper[target_table_name]["db_model"],
                                                             processed_table=processed_table
                                                             )
        return relation_level

    def _extra_foreign_table_from_declarative_base(self, model) -> Dict[str, Table]:
        mapper = inspect(model)
        foreign_key_table = {}
        reference_mapper = {}
        for r in mapper.relationships:
            local, = r.local_columns
            local = mapper.get_property_by_column(local).expression
            local_table = str(local).split('.')[0]
            local_column = str(local).split('.')[1]
            local_table_instance = local.table

            foreign_table = r.mapper.class_
            foreign_table_name = foreign_table.__tablename__
            foreign_secondary_table_name = ''
            if r.secondary_synchronize_pairs:
                # foreign_table_name = r.secondary.key
                foreign_secondary_table_name = str(r.secondary.key)

            local_reference_pairs = []
            '''
                        for i in r.synchronize_pairs:
                if r.secondary_synchronize_pairs:
                    local = str(i[0]).split('.')
                    reference = str(i[1]).split('.')
                    local_table_instance = i[0].table
                    reference_table_instance = i[1].table
                else:
                    local = str(r.local).split('.')
                    reference = str(i[0]).split('.')
                    local_table_instance = r.local.table
                    reference_table_instance = i[0].table
                local_table = local[0]
                local_column = local[1]
                reference_table = reference[0]
                reference_column = reference[1]
                self.reference_mapper[local_column] = foreign_table_name
                local_reference_pairs.append({'local': {"local_table": local_table,
                                                        "local_column": local_column},
                                              "reference": {"reference_table": reference_table,
                                                            "reference_column": reference_column},
                                              'local_table': local_table_instance,
                                              'local_table_columns': local_table_instance.c,
                                              'reference_table': reference_table_instance,
                                              'reference_table_columns': reference_table_instance.c})

            '''
            for i in r.synchronize_pairs:
                for column in i:
                    table_name_ = str(column).split('.')[0]
                    column_name_ = str(column).split('.')[1]
                    if table_name_ not in [foreign_secondary_table_name, foreign_table_name]:
                        continue

                    reference_table = table_name_
                    reference_column = column_name_
                    reference_table_instance = column.table
                    if r.secondary_synchronize_pairs:

                        exclude = True
                    else:

                        reference_mapper[local_column] = {"foreign_table": foreign_table,
                                                          "foreign_table_name": foreign_table_name}
                        exclude = False
                    local_reference_pairs.append({'local': {"local_table": local_table,
                                                            "local_column": local_column},
                                                  "reference": {"reference_table": reference_table,
                                                                "reference_column": reference_column},
                                                  'local_table': local_table_instance,
                                                  'local_table_columns': local_table_instance.c,
                                                  'reference_table': reference_table_instance,
                                                  'reference_table_columns': reference_table_instance.c,
                                                  'exclude': exclude})
            for i in r.secondary_synchronize_pairs:
                local_table_: str = None
                local_column_: str = None
                reference_table_: str = None
                reference_column_: str = None
                local_table_instance_: Table = None
                reference_table_instance_: Table = None
                for column in i:

                    table_name_ = str(column).split('.')[0]
                    column_name_ = str(column).split('.')[1]
                    if table_name_ == foreign_secondary_table_name:
                        local_table_ = str(column).split('.')[0]
                        local_column_ = str(column).split('.')[1]
                        local_table_instance_ = column.table
                    if table_name_ == foreign_table_name:
                        reference_table_ = str(column).split('.')[0]
                        reference_column_ = str(column).split('.')[1]
                        reference_table_instance_ = column.table

                reference_mapper[local_column_] = {"foreign_table": foreign_table,
                                                        "foreign_table_name": foreign_table_name}
                local_reference_pairs.append({'local': {"local_table": local_table_,
                                                        "local_column": local_column_},
                                              "reference": {"reference_table": reference_table_,
                                                            "reference_column": reference_column_},
                                              'local_table': local_table_instance_,
                                              'local_table_columns': local_table_instance_.c,
                                              'reference_table': reference_table_instance_,
                                              'reference_table_columns': reference_table_instance_.c,
                                              'exclude': False})

            all_fields_ = self._extract_all_field(foreign_table.__table__.c)
            response_fields = []
            for i in all_fields_:
                response_fields.append((i['column_name'],
                                        i['column_type'],
                                        None))
            response_model_dataclass = make_dataclass(
                f'foreign_{foreign_table_name + str(uuid.uuid4())}_FindManyResponseItemModel',
                response_fields,
            )
            response_item_model = _model_from_dataclass(response_model_dataclass)

            response_item_model = _add_orm_model_config_into_pydantic_model(response_item_model,
                                                                            config=OrmConfig)

            response_model = create_model(
                f'foreign_{foreign_table_name + str(uuid.uuid4())}_GetManyResponseForeignModel',
                **{'__root__': (Union[List[response_item_model], None], None)}
            )
            self.foreign_table_response_model_sets[foreign_table] = response_model
            foreign_key_table[foreign_table_name] = {'local_reference_pairs_set': local_reference_pairs,
                                                     'fields': all_fields_,
                                                     'instance': foreign_table,
                                                     'db_column': foreign_table}
        return foreign_key_table, reference_mapper

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
    def _assign_join_table_instance(request_or_response_object, join_table_mapping):
        received_request = deepcopy(request_or_response_object.__dict__)
        join_table_replace = {}
        if 'join_foreign_table' in received_request:
            for join_table in received_request['join_foreign_table']:
                if join_table in join_table_mapping:
                    join_table_replace[str(join_table)] = join_table_mapping[join_table]
            setattr(request_or_response_object, 'join_foreign_table', join_table_replace)

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
            elif column.primary_key and column.autoincrement == True:
                default = None
            else:
                default = ...
        else:
            if column.default is not None:
                default = column.default.arg
            else:
                default = None
        return default

    def _assign_str_matching_pattern(self, field_of_param: dict, result_: List[dict]) -> List[dict]:
        if self.sql_type == SqlType.postgresql:
            operator = List[PGSQLMatchingPatternInString]
        else:
            operator = List[MatchingPatternInStringBase]

        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str + ExtraFieldType.Matching_pattern,
             'column_type': Optional[operator],
             'column_default': [MatchingPatternInStringBase.case_sensitive],
             'column_description': ""},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.Str,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None,
             'column_description': field_of_param['column_description']}
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
                'column_default': ItemComparisonOperators.In,
                'column_description': ""},
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.List,
             'column_type': Optional[List[field_of_param['column_type']]],
             'column_default': None,
             'column_description': field_of_param['column_description']}

        ]:
            result_.append(i)
        return result_

    @staticmethod
    def _assign_range_comparison(field_of_param, result_: List[dict]) -> List[dict]:
        for i in [
            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.From}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeFromComparisonOperators],
             'column_default': RangeFromComparisonOperators.Greater_than_or_equal_to,
             'column_description': ""},

            {'column_name': field_of_param[
                                'column_name'] + f'{ExtraFieldTypePrefix.To}{ExtraFieldType.Comparison_operator}',
             'column_type': Optional[RangeToComparisonOperators],
             'column_default': RangeToComparisonOperators.Less_than.Less_than_or_equal_to,
             'column_description': ""},
        ]:
            result_.append(i)

        for i in [
            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.From,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.From, field_of_param['column_type'])],
             'column_default': None,
             'column_description': field_of_param['column_description']},

            {'column_name': field_of_param['column_name'] + ExtraFieldTypePrefix.To,
             'column_type': Optional[NewType(ExtraFieldTypePrefix.To, field_of_param['column_type'])],
             'column_default': None,
             'column_description': field_of_param['column_description']}
        ]:
            result_.append(i)
        return result_

    def _assign_foreign_join(self, result_, table_of_foreign=None) -> List[Union[Tuple, Dict]]:
        if table_of_foreign is None:
            table_of_foreign = self.table_of_foreign
        if not self.table_of_foreign:
            return result_
        table_name_enum = StrEnum('TableName' + str(uuid.uuid4()),
                                  {table_name: auto() for table_name in table_of_foreign})

        result_.append(('join_foreign_table', Optional[List[table_name_enum]], Query(None)))
        return result_

    def _get_fizzy_query_param(self, exclude_column: List[str] = None, fields=None) -> List[dict]:
        if not fields:
            fields = self.all_field
        if not exclude_column:
            exclude_column = []
        fields_: List[dict] = deepcopy(fields)
        result = []
        for field_ in fields_:
            if field_['column_name'] in exclude_column:
                continue
            if "column_foreign" in field_ and field_['column_foreign']:
                jump = False
                for foreign in field_['column_foreign']:
                    if foreign in exclude_column:
                        jump = True
                if jump:
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

    def _assign_pagination_param(self, result_: List[tuple]) -> List[Union[Tuple, Dict]]:
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
                    primary_name='any name of column')))
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
        conflict_model = make_dataclass(
            f'{self.db_name + str(uuid.uuid4())}_Upsert_one_request_update_columns_when_conflict_request_body_model',
            [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Body(i['column_default'], description=i['column_description'])))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'], description=i['column_description'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_Upsert_one_request_model',
                                            request_fields + on_conflict_handle,
                                            namespace={
                                                '__post_init__': lambda self_object: [i(self_object)
                                                                                      for i in request_validation]
                                            })

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_Upsert_one_response_model',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model = _to_require_but_default(response_model_pydantic)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
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
                                             'when the unique columns got conflict'))
        conflict_model = make_dataclass(
            f'{self.db_name + str(uuid.uuid4())}_Upsert_many_request_update_columns_when_conflict_request_body_model',
            [conflict_columns])
        on_conflict_handle = [('on_conflict', Optional[conflict_model],
                               Body(None))]

        # Ready the Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            insert_fields.append((i['column_name'],
                                  i['column_type'],
                                  field(default=Body(i['column_default'], description=i['column_description']))))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]

        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))

        insert_item_field_model_pydantic = make_dataclass(
            f'{self.db_name + str(uuid.uuid4())}_UpsertManyInsertItemRequestModel',
            insert_fields
        )

        # Create List Model with contains item
        insert_list_field = [('insert', List[insert_item_field_model_pydantic], Body(...))]
        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpsertManyRequestBody',
                                            insert_list_field + on_conflict_handle
                                            ,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]}
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpsertManyResponseItemModel',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_item_model = _to_require_but_default(response_model_pydantic)
        response_item_model = _add_orm_model_config_into_pydantic_model(response_item_model, config=OrmConfig)

        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_UpsertManyResponseListModel',
            **{'__root__': (List[response_item_model], None)}
        )

        return None, request_body_model, response_model

    def create_one(self) -> Tuple:
        request_validation = [lambda self_object: _filter_none(self_object)]
        request_fields = []
        response_fields = []


        # Create Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Body(i['column_default'], description=i['column_description'])))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'], description=i['column_description'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_Create_one_request_model',
                                            request_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [i(self_object)
                                                                                      for i in request_validation]
                                            })

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_Create_one_response_model',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model = _to_require_but_default(response_model_pydantic)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
        return None, request_body_model, response_model

    def create_many(self) -> Tuple:
        insert_fields = []
        response_fields = []

        # Ready the Request and Response Model
        all_field = deepcopy(self.all_field)
        for i in all_field:
            insert_fields.append((i['column_name'],
                                  i['column_type'],
                                  field(default=Body(i['column_default'], description=i['column_description']))))
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]

        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))

        insert_item_field_model_pydantic = make_dataclass(
            f'{self.db_name + str(uuid.uuid4())}_CreateManyInsertItemRequestModel',
            insert_fields
        )

        # Create List Model with contains item
        insert_list_field = [('insert', List[insert_item_field_model_pydantic], Body(...))]
        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_CreateManyRequestBody',
                                            insert_list_field
                                            ,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]}
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpsertManyResponseItemModel',
                                                  response_fields)
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_item_model = _to_require_but_default(response_model_pydantic)
        response_item_model = _add_orm_model_config_into_pydantic_model(response_item_model, config=OrmConfig)

        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_UpsertManyResponseListModel',
            **{'__root__': (List[response_item_model], None)}
        )

        return None, request_body_model, response_model

    def find_many(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param()
        query_param: List[Tuple] = self._assign_pagination_param(query_param)
        query_param: List[Union[Tuple, Dict]] = self._assign_foreign_join(query_param)

        response_fields = []
        all_field = deepcopy(self.all_field)
        for local_column, refer_table_info in self.reference_mapper.items():
            response_fields.append((f"{refer_table_info['foreign_table_name']}_foreign",
                                    self.foreign_table_response_model_sets[refer_table_info['foreign_table']],
                                    None))
        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    None))
            # i['column_type']))
        request_fields = []
        for i in query_param:
            assert isinstance(i, Tuple) or isinstance(i, dict)
            if isinstance(i, Tuple):
                request_fields.append(i)
            if isinstance(i, dict):
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.table_of_foreign:
            request_validation.append(lambda self_object: self._assign_join_table_instance(self_object,
                                                                                           self.table_of_foreign))
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))

        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_FindManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]}
                                             )
        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_FindManyResponseItemModel',
                                                  response_fields,
                                                  )
        response_list_item_model = _model_from_dataclass(response_model_dataclass)
        response_list_item_model = _add_orm_model_config_into_pydantic_model(response_list_item_model,
                                                                             config=OrmConfig)

        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_FindManyResponseListModel',
            **{'__root__': (Union[List[response_list_item_model], Any], None), '__base__': ExcludeUnsetBaseModel}
        )

        return request_query_model, None, response_model

    def _extra_relation_primary_key(self, relation_dbs):
        primary_key_columns = []
        foreign_table_name = ""
        primary_column_names = []
        for db_model_table in relation_dbs:
            table_name = db_model_table.key
            foreign_table_name += table_name + "_"
            primary_list = db_model_table.primary_key.columns.values()
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
                    f'and it is not nullable and in exclude_list'
                    f'it may throw error when you insert data ')
            description = self._get_field_description(primary_key_column)
            primary_column_name = str(primary_key_column.key)
            alias_primary_column_name = table_name + FOREIGN_PATH_PARAM_KEYWORD + str(primary_key_column.key)
            primary_column_names.append(alias_primary_column_name)
            primary_key_columns.append((alias_primary_column_name, column_type, Query(default,
                                                                                      description=description)))

        # TODO test foreign uuid key
        primary_columns_model: DataClassT = make_dataclass(f'{foreign_table_name + str(uuid.uuid4())}_PrimaryKeyModel',
                                                           primary_key_columns,
                                                           namespace={
                                                               '__post_init__': lambda
                                                                   self_object: self._value_of_list_to_str(
                                                                   self_object, self.uuid_type_columns)
                                                           })
        assert primary_column_names and primary_columns_model and primary_key_columns
        return primary_column_names, primary_columns_model, primary_key_columns

    def find_one(self) -> Tuple:
        query_param: List[dict] = self._get_fizzy_query_param(self.primary_key_str)
        query_param: List[Union[Tuple, Dict]] = self._assign_foreign_join(query_param)
        response_fields = []
        all_field = deepcopy(self.all_field)

        for local_column, refer_table_info in self.reference_mapper.items():
            response_fields.append((f"{refer_table_info['foreign_table_name']}_foreign",
                                    self.foreign_table_response_model_sets[refer_table_info['foreign_table']],
                                    None))

        for i in all_field:
            response_fields.append((i['column_name'],
                                    i['column_type'],
                                    Body(i['column_default'])))

        request_fields = []
        for i in query_param:
            assert isinstance(i, dict) or isinstance(i, tuple)
            if isinstance(i, Tuple):
                request_fields.append(i)
            else:
                request_fields.append((i['column_name'],
                                       i['column_type'],
                                       Query(i['column_default'], description=i['column_description'])))
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        if self.table_of_foreign:
            request_validation.append(lambda self_object: self._assign_join_table_instance(self_object,
                                                                                           self.table_of_foreign))

        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_FindOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_FindOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_FindOneResponseListModel',
            **{'__root__': (response_model, None), '__base__': ExcludeUnsetBaseModel}
        )

        return self._primary_key_dataclass_model, request_query_model, None, response_model, None

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
            assert isinstance(i, dict)
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Query(i['column_default'], description=i['column_description'])))
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_DeleteOneRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        response_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_DeleteOneResponseModel',
                                        response_fields,
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
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
            assert isinstance(i, dict)
            request_fields.append((i['column_name'],
                                   i['column_type'],
                                   Query(i['column_default'], description=i['column_description'])))
        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
            response_validation = [lambda self_object: self._value_of_list_to_str(self_object,
                                                                                  self.uuid_type_columns)]
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_DeleteManyRequestBody',
                                             request_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )
        # response_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_DeleteManyResponseModel',
        #                                 response_fields,
        #                                 namespace={
        #                                     '__post_init__': lambda self_object: [validator_(self_object)
        #                                                                           for validator_ in
        #                                                                           response_validation]}
        #                                 )
        response_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_DeleteManyResponseModel',
                                        response_fields,
                                        namespace={
                                            '__post_init__': lambda self_object: [validator_(self_object)
                                                                                  for validator_ in
                                                                                  response_validation]}
                                        )
        response_model = _model_from_dataclass(response_model)

        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_DeleteManyResponseListModel',
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
                                            Body(None, description=i['column_description'])))

        request_query_fields = []
        for i in query_param:
            assert isinstance(i, dict)
            request_query_fields.append((i['column_name'],
                                         i['column_type'],
                                         Query(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

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
            if i['column_name'] != self.primary_key_str:
                request_body_fields.append((i['column_name'],
                                            i['column_type'],
                                            Body(..., description=i['column_description'])))

        request_query_fields = []
        for i in query_param:
            assert isinstance(i, dict)
            request_query_fields.append((i['column_name'],
                                         i['column_type'],
                                         Query(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateOneRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateOneRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateOneResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model = _model_from_dataclass(response_model_dataclass)

        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)
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
                                            Body(..., description=i['column_description'])))

        request_query_fields = []
        for i in query_param:
            assert isinstance(i, dict)
            request_query_fields.append((i['column_name'],
                                         i['column_type'],
                                         Query(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_UpdateManyResponseModel',
                                                  response_fields,
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model_pydantic = _add_orm_model_config_into_pydantic_model(response_model_pydantic, config=OrmConfig)
        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_UpdateManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

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
                                            Body(None, description=i['column_description'])))

        request_query_fields = []
        for i in query_param:
            assert isinstance(i, dict)
            request_query_fields.append((i['column_name'],
                                         i['column_type'],
                                         Query(i['column_default'], description=i['column_description'])))

        request_validation = [lambda self_object: _filter_none(self_object)]
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        request_query_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchManyRequestQueryBody',
                                             request_query_fields,
                                             namespace={
                                                 '__post_init__': lambda self_object: [validator_(self_object)
                                                                                       for validator_ in
                                                                                       request_validation]
                                             }
                                             )

        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchManyRequestBodyBody',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator_(self_object)
                                                                                      for validator_ in
                                                                                      request_validation]
                                            }
                                            )

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PatchManyResponseModel',
                                                  response_fields,
                                                  namespace={
                                                      '__post_init__': lambda self_object: [validator_(self_object)
                                                                                            for validator_ in
                                                                                            request_validation]}
                                                  )
        response_model_pydantic = _model_from_dataclass(response_model_dataclass)

        response_model_pydantic = _add_orm_model_config_into_pydantic_model(response_model_pydantic, config=OrmConfig)
        response_model = create_model(
            f'{self.db_name + str(uuid.uuid4())}_PatchManyResponseListModel',
            **{'__root__': (List[response_model_pydantic], None)}
        )
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

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
                                        Body(i['column_default'], description=i['column_description'])))
            response_body_fields.append((i['column_name'],
                                         i['column_type'],
                                         Body(i['column_default'], description=i['column_description'])))

        # Ready the uuid to str validator
        if self.uuid_type_columns:
            request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                     self.uuid_type_columns))
        #
        request_body_model = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PostAndRedirectRequestModel',
                                            request_body_fields,
                                            namespace={
                                                '__post_init__': lambda self_object: [validator(self_object)
                                                                                      for validator in
                                                                                      request_validation]
                                            })

        response_model_dataclass = make_dataclass(f'{self.db_name + str(uuid.uuid4())}_PostAndRedirectResponseModel',
                                                  response_body_fields)
        response_model = _model_from_dataclass(response_model_dataclass)
        response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

        return None, request_body_model, response_model

    def foreign_tree_get_many(self) -> Tuple:
        _tmp = []
        path = ""
        path += '/{' + self.db_name + FOREIGN_PATH_PARAM_KEYWORD + self.primary_key_str + '}'
        path_model = [self.__db_model_table]
        pk_list = [self.db_name + "." + self.primary_key_str]
        total_table_of_foreign = {}
        function_name = "get_many_by_pk_from"
        for idx, relation in enumerate(self.relation_level):
            table_detail = self.foreign_mapper[relation]
            _all_fields = table_detail["all_fields"]
            _primary_key = table_detail["primary_key"]
            _db_name = table_detail["db_name"]
            _db_model = table_detail["db_model"]
            _db_model_table = table_detail["db_model_table"]
            _primary_key_dataclass_model = self._extra_relation_primary_key(path_model)
            path_model.append(_db_model_table)
            _query_param: List[dict] = self._get_fizzy_query_param(pk_list, _all_fields)
            table_of_foreign, reference_mapper = self.extra_foreign_table(_db_model)
            total_table_of_foreign.update(table_of_foreign)

            _query_param: List[Union[Tuple, Dict]] = self._assign_foreign_join(_query_param, table_of_foreign)
            response_fields = []
            all_field = deepcopy(_all_fields)
            path += '/' + _db_name + ''
            function_name += "_/_" + _db_name
            pk_list.append(_db_name + "." + _primary_key[0])

            for i in all_field:
                response_fields.append((i['column_name'],
                                        i['column_type'],
                                        Body(i['column_default'])))

            request_fields = []
            for i in _query_param:
                assert isinstance(i, dict) or isinstance(i, tuple)
                if isinstance(i, Tuple):
                    request_fields.append(i)
                else:
                    request_fields.append((i['column_name'],
                                           i['column_type'],
                                           Query(i['column_default'], description=i['column_description'])))
            request_validation = [lambda self_object: _filter_none(self_object)]

            if table_of_foreign:
                request_validation.append(lambda self_object: self._assign_join_table_instance(self_object,
                                                                                               total_table_of_foreign))
            if self.uuid_type_columns:
                request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                         self.uuid_type_columns))
            for local_column, refer_table_info in reference_mapper.items():
                response_fields.append((f"{refer_table_info['foreign_table_name']}_foreign",
                                        self.foreign_table_response_model_sets[refer_table_info['foreign_table']],
                                        None))

            request_query_model = make_dataclass(
                f'{"_".join(pk_list) + str(uuid.uuid4())}_FindOneForeignTreeRequestBody',
                request_fields,
                namespace={
                    '__post_init__': lambda self_object: [validator_(self_object)
                                                          for validator_ in
                                                          request_validation]}
            )
            response_model_dataclass = make_dataclass(f'{"_".join(pk_list) + str(uuid.uuid4())}_FindOneResponseModel',
                                                      response_fields,
                                                      namespace={
                                                          '__post_init__': lambda self_object: [validator_(self_object)
                                                                                                for validator_ in
                                                                                                request_validation]}
                                                      )
            response_model = _model_from_dataclass(response_model_dataclass)
            response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

            response_model = create_model(
                f'{"_".join(pk_list) + str(uuid.uuid4())}_FindManyResponseListModel',
                **{'__root__': (Union[List[response_model], Any], None), '__base__': ExcludeUnsetBaseModel}
            )

            _response_model = {}

            _response_model["primary_key_dataclass_model"] = _primary_key_dataclass_model[1]
            _response_model["request_query_model"] = request_query_model
            _response_model["response_model"] = response_model
            _response_model["path"] = path
            _response_model["function_name"] = function_name
            _tmp.append(_response_model)
            path += '/{' + _db_name + FOREIGN_PATH_PARAM_KEYWORD + _primary_key[0] + '}'

        return _tmp

    def foreign_tree_get_one(self) -> Tuple:
        _tmp = []
        path = ""
        path += '/{' + self.db_name + FOREIGN_PATH_PARAM_KEYWORD + self.primary_key_str + '}'
        path_model = [self.__db_model_table]
        pk_list = [self.db_name + "." + self.primary_key_str]
        total_table_of_foreign = {}
        function_name = "get_one_by_pk_from"

        for relation in self.relation_level:
            table_detail = self.foreign_mapper[relation]
            _all_fields = table_detail["all_fields"]
            _primary_key = table_detail["primary_key"]
            _db_name = table_detail["db_name"]
            _db_model = table_detail["db_model"]
            _db_model_table = table_detail["db_model_table"]
            path_model.append(_db_model_table)
            _primary_key_dataclass_model = self._extra_relation_primary_key(path_model)
            _query_param: List[dict] = self._get_fizzy_query_param([_primary_key[0]] + pk_list, _all_fields)
            table_of_foreign, reference_mapper = self.extra_foreign_table(_db_model)
            total_table_of_foreign.update(table_of_foreign)
            _query_param: List[Union[Tuple, Dict]] = self._assign_foreign_join(_query_param, table_of_foreign)
            response_fields = []
            all_field = deepcopy(_all_fields)

            path += '/' + _db_name + ''
            path += '/{' + _db_name + FOREIGN_PATH_PARAM_KEYWORD + _primary_key[0] + '}'
            function_name += "_/_" + _db_name

            pk_list.append(_db_name + "." + _primary_key[0])
            for i in all_field:
                response_fields.append((i['column_name'],
                                        i['column_type'],
                                        Body(i['column_default'])))

            request_fields = []
            for i in _query_param:
                assert isinstance(i, dict) or isinstance(i, tuple)
                if isinstance(i, Tuple):
                    request_fields.append(i)
                else:
                    request_fields.append((i['column_name'],
                                           i['column_type'],
                                           Query(i['column_default'], description=i['column_description'])))
            request_validation = [lambda self_object: _filter_none(self_object)]

            if table_of_foreign:
                request_validation.append(lambda self_object: self._assign_join_table_instance(self_object,
                                                                                               total_table_of_foreign))
            if self.uuid_type_columns:
                request_validation.append(lambda self_object: self._value_of_list_to_str(self_object,
                                                                                         self.uuid_type_columns))

            for local_column, refer_table_info in reference_mapper.items():
                response_fields.append((f"{refer_table_info['foreign_table_name']}_foreign",
                                        self.foreign_table_response_model_sets[refer_table_info['foreign_table']],
                                        None))

            request_query_model = make_dataclass(f'{"_".join(pk_list) + str(uuid.uuid4())}_FindOneRequestBody',
                                                 request_fields,
                                                 namespace={
                                                     '__post_init__': lambda self_object: [validator_(self_object)
                                                                                           for validator_ in
                                                                                           request_validation]
                                                 }
                                                 )

            response_model_dataclass = make_dataclass(f'{"_".join(pk_list) + str(uuid.uuid4())}_FindOneResponseModel',
                                                      response_fields,
                                                      namespace={
                                                          '__post_init__': lambda self_object: [validator_(self_object)
                                                                                                for validator_ in
                                                                                                request_validation]}
                                                      )
            response_model = _model_from_dataclass(response_model_dataclass)
            response_model = _add_orm_model_config_into_pydantic_model(response_model, config=OrmConfig)

            response_model = create_model(
                f'{"_".join(pk_list) + str(uuid.uuid4())}_FindOneResponseListModel',
                **{'__root__': (response_model, None), '__base__': ExcludeUnsetBaseModel}
            )
            _response_model = {}
            _response_model["primary_key_dataclass_model"] = _primary_key_dataclass_model[1]
            _response_model["request_query_model"] = request_query_model
            _response_model["response_model"] = response_model
            _response_model["path"] = path
            _response_model["function_name"] = function_name
            _tmp.append(_response_model)
        return _tmp
