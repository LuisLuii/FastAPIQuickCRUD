from enum import Enum, auto

from strenum import StrEnum


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
    DELETE_ONE = "DELETE_ONE"
    DELETE_MANY = "DELETE_MANY"
    POST_REDIRECT_GET = "POST_REDIRECT_GET"


class RequestMethods(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class CRUDRequestMapping(Enum):
    FIND_ONE = RequestMethods.GET
    FIND_MANY = RequestMethods.GET

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


class MatchingPatternInString(StrEnum):
    match_regex_with_case_sensitive = auto()
    match_regex_with_case_insensitive = auto()
    does_not_match_regex_with_case_sensitive = auto()
    does_not_match_regex_with_case_insensitive = auto()
    case_insensitive = auto()
    case_sensitive = auto()
    not_case_insensitive = auto()
    not_case_sensitive = auto()
    similar_to = auto()
    not_similar_to = auto()


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
