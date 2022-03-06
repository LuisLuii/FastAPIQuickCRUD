from enum import Enum, auto
from itertools import chain

from strenum import StrEnum

from .exceptions import InvalidRequestMethod


class SqlType(StrEnum):
    postgresql = auto()
    mysql = auto()
    mariadb = auto()
    sqlite = auto()
    oracle = auto()
    mssql = auto()

class Ordering(StrEnum):
    DESC = auto()
    ASC = auto()


class CrudMethods(Enum):
    FIND_ONE = "FIND_ONE"
    FIND_MANY = "FIND_MANY"
    UPDATE_ONE = "UPDATE_ONE"
    UPDATE_MANY = "UPDATE_MANY"
    PATCH_ONE = "PATCH_ONE"
    PATCH_MANY = "PATCH_MANY"
    UPSERT_ONE = "UPSERT_ONE"
    UPSERT_MANY = "UPSERT_MANY"
    CREATE_ONE = "CREATE_ONE"
    CREATE_MANY = "CREATE_MANY"
    DELETE_ONE = "DELETE_ONE"
    DELETE_MANY = "DELETE_MANY"
    POST_REDIRECT_GET = "POST_REDIRECT_GET"
    FIND_ONE_WITH_FOREIGN_TREE = "FIND_ONE_WITH_FOREIGN_TREE"
    FIND_MANY_WITH_FOREIGN_TREE = "FIND_MANY_WITH_FOREIGN_TREE"

    @staticmethod
    def get_table_full_crud_method():
        return [CrudMethods.FIND_MANY, CrudMethods.CREATE_MANY, CrudMethods.UPDATE_MANY, CrudMethods.PATCH_MANY,
                CrudMethods.DELETE_MANY]

    @staticmethod
    def get_declarative_model_full_crud_method():
        return [CrudMethods.FIND_MANY, CrudMethods.FIND_ONE,
                CrudMethods.UPDATE_MANY, CrudMethods.UPDATE_ONE,
                CrudMethods.PATCH_MANY, CrudMethods.PATCH_ONE, CrudMethods.CREATE_MANY,
                 CrudMethods.DELETE_MANY, CrudMethods.DELETE_ONE, CrudMethods.FIND_ONE_WITH_FOREIGN_TREE,
                 CrudMethods.FIND_MANY_WITH_FOREIGN_TREE]


class RequestMethods(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class CRUDRequestMapping(Enum):
    FIND_ONE = RequestMethods.GET
    FIND_ONE_WITH_FOREIGN_TREE = RequestMethods.GET

    FIND_MANY = RequestMethods.GET
    FIND_MANY_WITH_FOREIGN_TREE = RequestMethods.GET

    UPDATE_ONE = RequestMethods.PUT
    UPDATE_MANY = RequestMethods.PUT

    PATCH_ONE = RequestMethods.PATCH
    PATCH_MANY = RequestMethods.PATCH

    CREATE_ONE = RequestMethods.POST
    CREATE_MANY = RequestMethods.POST

    UPSERT_ONE = RequestMethods.POST
    UPSERT_MANY = RequestMethods.POST

    DELETE_ONE = RequestMethods.DELETE
    DELETE_MANY = RequestMethods.DELETE

    GET_VIEW = RequestMethods.GET
    POST_REDIRECT_GET = RequestMethods.POST

    @classmethod
    def get_request_method_by_crud_method(cls, value):
        crud_methods = cls.__dict__
        if value not in crud_methods:
            raise InvalidRequestMethod(
                f'{value} is not an available request method, Please use CrudMethods to select available crud method')
        return crud_methods[value].value


class ExtraFieldType(StrEnum):
    Comparison_operator = '_____comparison_operator'
    Matching_pattern = '_____matching_pattern'


class ExtraFieldTypePrefix(StrEnum):
    List = '____list'
    From = '____from'
    To = '____to'
    Str = '____str'


class RangeFromComparisonOperators(StrEnum):
    Greater_than = auto()
    Greater_than_or_equal_to = auto()


class RangeToComparisonOperators(StrEnum):
    Less_than = auto()
    Less_than_or_equal_to = auto()


class ItemComparisonOperators(StrEnum):
    Equal = auto()
    Not_equal = auto()
    In = auto()
    Not_in = auto()


class MatchingPatternInStringBase(StrEnum):
    case_insensitive = auto()
    case_sensitive = auto()
    not_case_insensitive = auto()
    not_case_sensitive = auto()
    contains = auto()


class PGSQLMatchingPattern(StrEnum):
    match_regex_with_case_sensitive = auto()
    match_regex_with_case_insensitive = auto()
    does_not_match_regex_with_case_sensitive = auto()
    does_not_match_regex_with_case_insensitive = auto()
    similar_to = auto()
    not_similar_to = auto()


PGSQLMatchingPatternInString = StrEnum('PGSQLMatchingPatternInString',
                                       {Pattern: auto() for Pattern in
                                        chain(MatchingPatternInStringBase, PGSQLMatchingPattern)})


class JSONMatchingMode(str, Enum):
    match_the_key_value = 'match_the_key_value'
    match_the_value_if_not_null_by_key = 'match_the_value_if_not_null_by_key'
    custom_query = 'custom_query'


class JSONBMatchingMode(str, Enum):
    match_the_key_value = 'match_the_key_value'
    match_the_value_if_not_null_by_key = 'match_the_value_if_not_null_by_key'
    custom_query = 'custom_query'


class SessionObject(StrEnum):
    sqlalchemy = auto()
    databases = auto()

FOREIGN_PATH_PARAM_KEYWORD = "__pk__"