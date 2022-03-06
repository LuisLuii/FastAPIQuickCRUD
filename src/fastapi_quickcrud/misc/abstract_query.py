from abc import ABC
from typing import List, Union

from sqlalchemy import and_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.schema import Table

from .exceptions import UnknownOrderType, UnknownColumn, UpdateColumnEmptyException
from .type import Ordering
from .utils import clean_input_fields, path_query_builder
from .utils import find_query_builder


class SQLAlchemyGeneralSQLQueryService(ABC):

    def __init__(self, *, model, async_mode, foreign_table_mapping):

        """
        :param model: declarative_base model
        :param async_mode: bool
        """

        self.model = model
        self.model_columns = model
        self.async_mode = async_mode
        self.foreign_table_mapping = foreign_table_mapping

    def get_many(self, *,
                 join_mode,
                 query,
                 target_model=None,
                 abstract_param=None
                 ) -> BinaryExpression:
        filter_args = query
        limit = filter_args.pop('limit', None)
        offset = filter_args.pop('offset', None)
        order_by_columns = filter_args.pop('order_by_columns', None)
        model = self.model
        if target_model:
            model = self.foreign_table_mapping[target_model]
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=model)
        path_filter_list: List[BinaryExpression] = path_query_builder(params=abstract_param,
                                                                      model=self.foreign_table_mapping)
        join_table_instance_list: list = self.get_join_select_fields(join_mode)


        if not isinstance(self.model, Table):
            model = model.__table__

        stmt = select(*[model] + join_table_instance_list).filter(and_(*filter_list+path_filter_list))
        if order_by_columns:
            order_by_query_list = []

            for order_by_column in order_by_columns:
                if not order_by_column:
                    continue
                sort_column, order_by = (order_by_column.replace(' ', '').split(':') + [None])[:2]
                if not hasattr(self.model_columns, sort_column):
                    raise UnknownColumn(f'column {sort_column} is not exited')
                if not order_by:
                    order_by_query_list.append(getattr(self.model_columns, sort_column).asc())
                elif order_by.upper() == Ordering.DESC.upper():
                    order_by_query_list.append(getattr(self.model_columns, sort_column).desc())
                elif order_by.upper() == Ordering.ASC.upper():
                    order_by_query_list.append(getattr(self.model_columns, sort_column).asc())
                else:
                    raise UnknownOrderType(f"Unknown order type {order_by}, only accept DESC or ASC")
            if order_by_query_list:
                stmt = stmt.order_by(*order_by_query_list)
        stmt = stmt.limit(limit).offset(offset)
        stmt = self.get_join_by_excpression(stmt, join_mode=join_mode)
        return stmt

    def get_one(self, *,
                extra_args: dict,
                filter_args: dict,
                join_mode=None
                ) -> BinaryExpression:
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)

        extra_query_expression: List[BinaryExpression] = find_query_builder(param=extra_args,
                                                                            model=self.model)
        join_table_instance_list: list = self.get_join_select_fields(join_mode)
        model = self.model
        if not isinstance(self.model, Table):
            model = model.__table__
        stmt = select(*[model] + join_table_instance_list).where(and_(*filter_list + extra_query_expression))
        # stmt = session.query(*[model] + join_table_instance_list).filter(and_(*filter_list + extra_query_expression))
        stmt = self.get_join_by_excpression(stmt, join_mode=join_mode)
        return stmt

    def create(self, *,
               insert_arg,
               create_one=True,
               ) -> List[BinaryExpression]:
        insert_arg_dict: Union[list, dict] = insert_arg
        if not create_one:
            insert_arg_list: list = insert_arg_dict.pop('insert', None)
            insert_arg_dict = []
            for i in insert_arg_list:
                insert_arg_dict.append(i.__dict__)
        if not isinstance(insert_arg_dict, list):
            insert_arg_dict = [insert_arg_dict]

        insert_arg_dict: list[dict] = [clean_input_fields(model=self.model_columns, param=insert_arg)
                                       for insert_arg in insert_arg_dict]
        if isinstance(insert_arg_dict, list):
            new_data = []
            for i in insert_arg_dict:
                new_data.append(self.model(**i))
        return new_data

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError

    def insert_one(self, *,
                   insert_args) -> BinaryExpression:
        insert_args = insert_args
        update_columns = clean_input_fields(insert_args,
                                            self.model_columns)
        inserted_instance = self.model(**update_columns)
        return inserted_instance

    def get_join_select_fields(self, join_mode=None):
        join_table_instance_list = []
        if not join_mode:
            return join_table_instance_list
        for _, table_instance in join_mode.items():
            for local_reference in table_instance['local_reference_pairs_set']:
                if 'exclude' in local_reference and local_reference['exclude']:
                    continue
                for column in local_reference['reference_table_columns']:
                    foreign_table_name = local_reference['reference']['reference_table']
                    join_table_instance_list.append(
                        column.label(foreign_table_name + '_foreign_____' + str(column).split('.')[1]))
        return join_table_instance_list

    def get_join_by_excpression(self, stmt: BinaryExpression, join_mode=None) -> BinaryExpression:
        if not join_mode:
            return stmt
        for join_table, data in join_mode.items():
            for local_reference in data['local_reference_pairs_set']:
                local = local_reference['local']['local_column']
                reference = local_reference['reference']['reference_column']
                local_column = getattr(local_reference['local_table_columns'], local)
                reference_column = getattr(local_reference['reference_table_columns'], reference)
                table = local_reference['reference_table']
                stmt = stmt.join(table, local_column == reference_column)
        return stmt

    # def delete(self,
    #            *,
    #            delete_args: dict,
    #            session,
    #            primary_key: dict = None,
    #            ) -> BinaryExpression:
    #     filter_list: List[BinaryExpression] = find_query_builder(param=delete_args,
    #                                                              model=self.model_columns)
    #     if primary_key:
    #         filter_list += find_query_builder(param=primary_key,
    #                                           model=self.model_columns)
    #
    #     delete_instance = session.query(self.model).where(and_(*filter_list))
    #     return delete_instance

    def model_query(self,
                    *,
                    session,
                    extra_args: dict = None,
                    filter_args: dict = None,
                    ) -> BinaryExpression:

        '''
        used for delette and update
        '''

        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)
        if extra_args:
            filter_list += find_query_builder(param=extra_args,
                                              model=self.model_columns)
        stmt = select(self.model).where(and_(*filter_list))
        return stmt

    def get_one_with_foreign_pk(self, *,
                                 join_mode,
                                 query,
                                 target_model,
                                 abstract_param=None
                                 ) -> BinaryExpression:
        model = self.foreign_table_mapping[target_model]
        filter_list: List[BinaryExpression] = find_query_builder(param=query,
                                                                 model=model)
        path_filter_list: List[BinaryExpression] = path_query_builder(params=abstract_param,
                                                                      model=self.foreign_table_mapping)
        join_table_instance_list: list = self.get_join_select_fields(join_mode)

        if not isinstance(self.model, Table):
            model = model.__table__

        stmt = select(*[model] + join_table_instance_list).filter(and_(*filter_list + path_filter_list))

        stmt = self.get_join_by_excpression(stmt, join_mode=join_mode)
        return stmt


    # def update(self, *,
    #            update_args,
    #            extra_query,
    #            session,
    #            primary_key=None,
    #            ) -> BinaryExpression:
    #
    #
    #     filter_list: List[BinaryExpression] = find_query_builder(param=extra_query,
    #                                                              model=self.model_columns)
    #     if primary_key:
    #         primary_key = primary_key
    #         filter_list += find_query_builder(param=primary_key, model=self.model_columns)
    #     update_stmt = update(self.model).where(and_(*filter_list)).values(update_args)
    #     update_stmt = update_stmt.execution_options(synchronize_session=False)
    #     return update_stmt


class SQLAlchemyPGSQLQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):

        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super(SQLAlchemyPGSQLQueryService,
              self).__init__(model=model,
                             async_mode=async_mode,
                             foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        insert_arg_dict: Union[list, dict] = insert_arg

        insert_with_conflict_handle = insert_arg_dict.pop('on_conflict', None)
        if not upsert_one:
            insert_arg_list: list = insert_arg_dict.pop('insert', None)
            insert_arg_dict = []
            for i in insert_arg_list:
                insert_arg_dict.append(i.__dict__)

        if not isinstance(insert_arg_dict, list):
            insert_arg_dict: list[dict] = [insert_arg_dict]
        insert_arg_dict: list[dict] = [clean_input_fields(model=self.model_columns, param=insert_arg)
                                       for insert_arg in insert_arg_dict]
        insert_stmt = insert(self.model).values(insert_arg_dict)

        if unique_fields and insert_with_conflict_handle:
            update_columns = clean_input_fields(insert_with_conflict_handle.__dict__.get('update_columns', None),
                                                self.model_columns)
            if not update_columns:
                raise UpdateColumnEmptyException('update_columns parameter must be a non-empty list ')
            conflict_update_dict = {}
            for columns in update_columns:
                conflict_update_dict[columns] = getattr(insert_stmt.excluded, columns)

            conflict_list = clean_input_fields(model=self.model_columns, param=unique_fields)
            conflict_update_dict = clean_input_fields(model=self.model_columns, param=conflict_update_dict)
            insert_stmt = insert_stmt.on_conflict_do_update(index_elements=conflict_list,
                                                            set_=conflict_update_dict
                                                            )
        insert_stmt = insert_stmt.returning(text('*'))
        return insert_stmt


class SQLAlchemySQLITEQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError


class SQLAlchemyMySQLQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError


class SQLAlchemyMariaDBQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError


class SQLAlchemyOracleQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError


class SQLAlchemyMSSqlQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError


class SQLAlchemyNotSupportQueryService(SQLAlchemyGeneralSQLQueryService):

    def __init__(self, *, model, async_mode, foreign_table_mapping):
        """
        :param model: declarative_base model
        :param async_mode: bool
        """
        super().__init__(model=model,
                         async_mode=async_mode,
                         foreign_table_mapping=foreign_table_mapping)
        self.model = model
        self.model_columns = model
        self.async_mode = async_mode

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        raise NotImplementedError
