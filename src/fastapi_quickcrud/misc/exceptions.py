from fastapi import HTTPException


class FindOneApiNotRegister(HTTPException):
    pass


class CRUDBuilderException(BaseException):
    pass


class RequestMissing(CRUDBuilderException):
    pass

class PrimaryMissing(CRUDBuilderException):
    pass


class UnknownOrderType(CRUDBuilderException):
    pass


class UpdateColumnEmptyException(CRUDBuilderException):
    pass


class UnknownColumn(CRUDBuilderException):
    pass


class QueryOperatorNotFound(CRUDBuilderException):
    pass


class UnknownError(CRUDBuilderException):
    pass


class ConflictColumnsCannotHit(CRUDBuilderException):
    pass


class MultipleSingleUniqueNotSupportedException(CRUDBuilderException):
    pass


class SchemaException(CRUDBuilderException):
    pass


class CompositePrimaryKeyConstraintNotSupportedException(CRUDBuilderException):
    pass


class MultiplePrimaryKeyNotSupportedException(CRUDBuilderException):
    pass


class ColumnTypeNotSupportedException(CRUDBuilderException):
    pass


class InvalidRequestMethod(CRUDBuilderException):
    pass


class RequestResponseModelMissingException(Exception):
    def __init__(self, msg=""):
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        return self.msg


class ConflictException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)

    def __str__(self) -> str:
        return self.msg


#
# class NotFoundError(MongoQueryError):
#     def __init__(self, Collection: Type[ModelType], model: BaseModel):
#         detail = "does not exist"
#         super().__init__(Collection, model, detail)
#
#
#
# class DuplicatedError(MongoQueryError):
#     def __init__(self, Collection: Type[ModelType], model: BaseModel):
#         detail = "was already existed"
#         super().__init__(Collection, model, detail)

class FDDRestHTTPException(HTTPException):
    """Baseclass for all HTTP exceptions in FDD Rest API.  This exception can be called as WSGI
        application to render a default error page or you can catch the subclasses
        of it independently and render nicer error messages.
        """
