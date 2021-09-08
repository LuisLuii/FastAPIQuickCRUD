from typing import List, Union

from sqlalchemy import and_, text, select, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.schema import Table

from .exceptions import UnknownOrderType, UpdateColumnEmptyException, UnknownColumn
from .type import Ordering
from .utils import clean_input_fields
from .utils import find_query_builder


#
# class DBQueryServiceBase(ABC):
#
#     @abstractmethod
#     def insert_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def get_many(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def get_one(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def upsert(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def delete(self):
#         raise NotImplementedError
#
#     @abstractmethod
#     def update(self):
#         raise NotImplementedError


class SQLAlchemyQueryService(object):

    def __init__(self, *, model, async_mode):

        """
        :param model: declarative_base model
        :param async_mode: bool
        """

        if isinstance(model, Table):
            self.model = model
            self.model_columns = model.c
        else:
            self.model = model
            self.model_columns = model
        self.async_mode = async_mode

    def insert_one(self, *,
                   insert_args) -> BinaryExpression:
        insert_args = insert_args.__dict__
        update_columns = clean_input_fields(insert_args,
                                            self.model_columns)
        insert_stmt = insert(self.model).values(update_columns)
        insert_stmt = insert_stmt.returning(text("*"))
        return insert_stmt

    def get_join_select_fields(self, join_mode = None):
        join_table_instance_list = []
        if not join_mode:
            return join_table_instance_list
        for table_name, table_instance in join_mode.items():
            for local_reference in table_instance['local_reference_pairs_set']:
                if 'exclude' in local_reference and local_reference['exclude']:
                    continue
                for column in local_reference['reference_table_columns']:
                    foreign_name = local_reference['local']['local_column']
                    join_table_instance_list.append(
                        column.label(foreign_name + '_foreign_____' + str(column).split('.')[1]))
        return join_table_instance_list


    def get_join_by_excpression(self,stmt: BinaryExpression, join_mode = None) -> BinaryExpression:
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

    def get_many(self, *,
                 join_mode,
                 query,
                 ) -> BinaryExpression:
        filter_args = query.__dict__
        limit = filter_args.pop('limit', None)
        offset = filter_args.pop('offset', None)
        order_by_columns = filter_args.pop('order_by_columns', None)
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)
        join_table_instance_list: list = self.get_join_select_fields(join_mode)

        if not isinstance(self.model, Table):
            model = self.model.__table__
        else:
            model = self.model

        stmt = select(*[model] + join_table_instance_list).where(and_(*filter_list))
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
        stmt = self.get_join_by_excpression(stmt,join_mode=join_mode)

        return stmt

    def get_one(self, *,
                extra_args,
                filter_args,
                join_mode
                ) -> BinaryExpression:
        filter_args = filter_args.__dict__
        extra_args = extra_args.__dict__
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)

        extra_query_expression: List[BinaryExpression] = find_query_builder(param=extra_args,
                                                                            model=self.model_columns)
        join_table_instance_list: list = self.get_join_select_fields(join_mode)
        if not isinstance(self.model, Table):
            model = self.model.__table__
        else:
            model = self.model

        stmt = select(*[model] + join_table_instance_list).where(and_(*filter_list + extra_query_expression))
        stmt = self.get_join_by_excpression(stmt, join_mode=join_mode)
        return stmt

    def upsert(self, *,
               insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ) -> BinaryExpression:
        insert_arg_dict: Union[list, dict] = insert_arg.__dict__

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
        # if upsert_one:
        #     query_result, = query_result
        return insert_stmt

    def delete(self,
               *,
               delete_args,
               primary_key=None,
               ) -> BinaryExpression:
        delete_args = delete_args.__dict__
        filter_list: List[BinaryExpression] = find_query_builder(param=delete_args,
                                                                 model=self.model_columns)
        if primary_key:
            primary_key = primary_key.__dict__
            filter_list += find_query_builder(param=primary_key,
                                              model=self.model_columns)

        delete_stmt = delete(self.model).where(and_(*filter_list))
        delete_stmt = delete_stmt.returning(text('*'))
        delete_stmt = delete_stmt.execution_options(synchronize_session=False)
        return delete_stmt

    def update(self, *,
               update_args,
               extra_query,
               primary_key=None,
               ) -> BinaryExpression:
        update_args = update_args.__dict__
        extra_query = extra_query.__dict__
        filter_list: List[BinaryExpression] = find_query_builder(param=extra_query,
                                                                 model=self.model_columns)
        if primary_key:
            primary_key = primary_key.__dict__
            filter_list += find_query_builder(param=primary_key, model=self.model_columns)
        update_stmt = update(self.model).where(and_(*filter_list)).values(update_args)
        update_stmt = update_stmt.returning(text('*'))
        update_stmt = update_stmt.execution_options(synchronize_session=False)
        return update_stmt
