# from typing import List, TypeVar
#
# from sqlalchemy import and_, text, select, delete, update
# from sqlalchemy.dialects.postgresql import insert
# # from sqlalchemy.engine import ChunkedIteratorResult, CursorResult
# from sqlalchemy.sql.elements import BinaryExpression
#
# from .misc.exceptions import UnknownOrderType, UpdateColumnEmptyException, UnknownColumn
# from .misc.type import Ordering
# from .misc.utils import Base, alias_to_column
# from .misc.utils import find_query_builder
#
#
# SchemaModelType = TypeVar("SchemaModelType", bound=Base)
#
#
#
#
# class CrudService:
#     def __init__(
#             self,
#             *,
#             model,
#     ):
#
#         self.model = model
#
#     def insert_one(self,
#                    insert_args,
#                    session) -> List[SchemaModelType]:
#
#         insert_arg_dict: list[dict] = alias_to_column(model=self.model, param=insert_args)
#         insert_stmt = insert(self.model).values([insert_arg_dict])
#         insert_stmt = insert_stmt.returning(text("*"))
#         return insert_stmt
#
#     def get_many(self,
#                  *,
#                  filter_args,
#                  limit,
#                  offset,
#                  order_by_columns,
#                  session):
#                  # session) -> ChunkedIteratorResult:
#
#         filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
#                                                                  model=self.model)
#         stmt = select(self.model).where(and_(*filter_list))
#         if order_by_columns:
#             order_by_query_list = []
#             for order_by_column in order_by_columns:
#                 sort_column, order_by = (order_by_column.replace(' ', '').split(':') + [None])[:2]
#                 if not order_by:
#                     order_by_query_list.append(getattr(self.model, sort_column).asc())
#                 elif order_by.upper() == Ordering.DESC.upper():
#                     order_by_query_list.append(getattr(self.model, sort_column).desc())
#                 elif order_by.upper() == Ordering.ASC.upper():
#                     order_by_query_list.append(getattr(self.model, sort_column).asc())
#                 else:
#                     raise UnknownOrderType(f"Unknown order type {order_by}, oly accept DESC or ASC")
#             stmt = stmt.order_by(*order_by_query_list)
#         stmt = stmt.limit(limit).offset(offset)
#         return stmt
#
#     def get_one(self,
#                 *,
#                 extra_args,
#                 filter_args) :
#                 # session) -> ChunkedIteratorResult:
#
#         filter_list: List[BinaryExpression] = find_query_builder(param=filter_args,
#                                                                  model=self.model)
#
#         extra_query_expression: List[BinaryExpression] = find_query_builder(param=extra_args,
#                                                                             model=self.model)
#         stmt = select(self.model).where(and_(*filter_list + extra_query_expression))
#         return stmt
#
#     def upsert(self,
#                insert_arg,
#                unique_fields: List[str],
#                session,
#                upsert_one=True):
#                # upsert_one=True) -> CursorResult:
#         insert_arg_dict: dict = insert_arg.__dict__
#
#         insert_with_conflict_handle = insert_arg_dict.pop('on_conflict', None)
#         if not upsert_one:
#             insert_arg_list: list = insert_arg_dict.pop('insert', None)
#             insert_arg_dict = []
#             for i in insert_arg_list:
#                 insert_arg_dict.append(i.__dict__)
#
#         if not isinstance(insert_arg_dict, list):
#             insert_arg_dict: list[dict] = [insert_arg_dict]
#         insert_arg_dict: list[dict] = [alias_to_column(model=self.model, param=insert_arg)
#                                        for insert_arg in insert_arg_dict]
#         insert_stmt = insert(self.model).values(insert_arg_dict)
#
#         if unique_fields and insert_with_conflict_handle:
#             update_columns = alias_to_column(insert_with_conflict_handle.__dict__.get('update_columns', None),
#                                              self.model)
#             if not update_columns:
#                 raise UpdateColumnEmptyException('update_columns parameter must be a non-empty list ')
#             conflict_update_dict = {}
#             for columns in update_columns:
#                 if hasattr(insert_stmt.excluded, columns):
#                     conflict_update_dict[columns] = getattr(insert_stmt.excluded, columns)
#                 else:
#                     raise UnknownColumn(f'the {columns} is not exited')
#             conflict_list = alias_to_column(model=self.model, param=unique_fields)
#             conflict_update_dict = alias_to_column(model=self.model,
#                                                       param=conflict_update_dict,
#                                                       column_collection=True)
#             insert_stmt = insert_stmt.on_conflict_do_update(index_elements=conflict_list,
#                                                             set_=conflict_update_dict
#                                                             )
#         insert_stmt = insert_stmt.returning(text('*'))
#
#         # input_field_list = [k for i in insert_arg_dicts for k in i]
#         # for conflict_field in conflict_list:
#         #     if conflict_field not in input_field_list:
#         #         raise Exception(f'{conflict_field} is required to input, when you used it in on_conflict_columns')
#
#         # FIXME handle by user
#
#         return insert_stmt
#
#     def delete(self,
#                *,
#                delete_args,
#                session,
#                primary_key=None):
#
#         filter_list: List[BinaryExpression] = find_query_builder(param=delete_args,
#                                                                  model=self.model)
#         if primary_key:
#             filter_list += find_query_builder(param=primary_key,
#                                               model=self.model)
#
#         delete_stmt = delete(self.model).where(and_(*filter_list))
#         delete_stmt = delete_stmt.returning(text('*'))
#         delete_stmt = delete_stmt.execution_options(synchronize_session=False)
#         return delete_stmt
#
#     def update(self,
#                update_args,
#                extra_query,
#                session,
#                primary_key=None
#                ):
#         filter_list: List[BinaryExpression] = find_query_builder(param=extra_query,
#                                                                  model=self.model)
#         if primary_key:
#             filter_list += find_query_builder(param=primary_key, model=self.model)
#         # update_num = session.query(self.model).filter(and_(*filter_list)). \
#         #     update(update_args, synchronize_session='fetch')
#         update_stmt = update(self.model).where(and_(*filter_list)).values(update_args)
#         update_stmt = update_stmt.returning(text('*'))
#         update_stmt = update_stmt.execution_options(synchronize_session=False)
#         return update_stmt
#
