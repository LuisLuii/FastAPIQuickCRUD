from typing import List, Union

from sqlalchemy import and_, text, select, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.schema import Table
from .exceptions import UnknownOrderType, UpdateColumnEmptyException, UnknownColumn
from .type import Ordering
from .utils import alias_to_column
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

    @staticmethod
    async def async_execute(*, session, stmt):
        query_result = session.execute(stmt)
        query_result = await query_result
        return query_result

    @staticmethod
    def execute(*, session, stmt):
        query_result = session.execute(stmt)
        query_result = query_result
        return query_result

    def insert_one(self, *,
                   insert_args):
        insert_args = insert_args.__dict__
        update_columns = alias_to_column(insert_args,
                                         self.model_columns)
        insert_stmt = insert(self.model).values(update_columns)
        insert_stmt = insert_stmt.returning(text("*"))
        return insert_stmt

    def get_many(self, *,
                 query,
                 ):
        filter_args = query.__dict__
        limit = filter_args.pop('limit', None)
        offset = filter_args.pop('offset', None)
        order_by_columns = filter_args.pop('order_by_columns', None)
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)
        stmt = select(self.model).where(and_(*filter_list))
        if order_by_columns:
            order_by_query_list = []
            for order_by_column in order_by_columns:
                sort_column, order_by = (order_by_column.replace(' ', '').split(':') + [None])[:2]
                if not order_by:
                    order_by_query_list.append(getattr(self.model_columns, sort_column).asc())
                elif order_by.upper() == Ordering.DESC.upper():
                    order_by_query_list.append(getattr(self.model_columns, sort_column).desc())
                elif order_by.upper() == Ordering.ASC.upper():
                    order_by_query_list.append(getattr(self.model_columns, sort_column).asc())
                else:
                    raise UnknownOrderType(f"Unknown order type {order_by}, oly accept DESC or ASC")
            stmt = stmt.order_by(*order_by_query_list)
        stmt = stmt.limit(limit).offset(offset)
        return stmt

    def get_one(self, *,
                extra_args,
                filter_args,
                ):
        filter_args = filter_args.__dict__
        extra_args = extra_args.__dict__
        filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
                                                                 model=self.model_columns)

        extra_query_expression: List[BinaryExpression] = find_query_builder(param=extra_args,
                                                                            model=self.model_columns)
        stmt = select(self.model).where(and_(*filter_list + extra_query_expression))
        return stmt

    def upsert(self, *, insert_arg,
               unique_fields: List[str],
               upsert_one=True,
               ):
        insert_arg_dict: Union[list, dict] = insert_arg.__dict__

        insert_with_conflict_handle = insert_arg_dict.pop('on_conflict', None)
        if not upsert_one:
            insert_arg_list: list = insert_arg_dict.pop('insert', None)
            insert_arg_dict = []
            for i in insert_arg_list:
                insert_arg_dict.append(i.__dict__)

        if not isinstance(insert_arg_dict, list):
            insert_arg_dict: list[dict] = [insert_arg_dict]
        insert_arg_dict: list[dict] = [alias_to_column(model=self.model_columns, param=insert_arg)
                                       for insert_arg in insert_arg_dict]
        insert_stmt = insert(self.model).values(insert_arg_dict)

        if unique_fields and insert_with_conflict_handle:
            update_columns = alias_to_column(insert_with_conflict_handle.__dict__.get('update_columns', None),
                                             self.model_columns)
            if not update_columns:
                raise UpdateColumnEmptyException('update_columns parameter must be a non-empty list ')
            conflict_update_dict = {}
            for columns in update_columns:
                if hasattr(insert_stmt.excluded, columns):
                    conflict_update_dict[columns] = getattr(insert_stmt.excluded, columns)
                else:
                    raise UnknownColumn(f'the {columns} is not exited')
            conflict_list = alias_to_column(model=self.model_columns, param=unique_fields)
            conflict_update_dict = alias_to_column(model=self.model_columns, param=conflict_update_dict, column_collection=True)
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
               ):
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
               ):
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
