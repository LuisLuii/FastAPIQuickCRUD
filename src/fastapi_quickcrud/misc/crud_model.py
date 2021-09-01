from typing import Optional, Dict, List

from pydantic import BaseModel
from pydantic.main import ModelMetaclass

from .exceptions import RequestMissing, InvalidRequestMethod
from .type import CrudMethods


class RequestResponseModel(BaseModel):
    requestUrlParamModel: Optional[ModelMetaclass]
    requestQueryModel: Optional[ModelMetaclass]
    requestBodyModel: Optional[ModelMetaclass]
    responseModel: Optional[ModelMetaclass]
    jsonRequestFieldModel: Optional[ModelMetaclass]
    jsonbRequestFieldModel: Optional[ModelMetaclass]
    arrayRequestFieldModel: Optional[ModelMetaclass]


class CRUDModel(BaseModel):
    GET: Optional[Dict[CrudMethods, RequestResponseModel]]
    POST: Optional[Dict[CrudMethods, RequestResponseModel]]
    PUT: Optional[Dict[CrudMethods, RequestResponseModel]]
    PATCH: Optional[Dict[CrudMethods, RequestResponseModel]]
    DELETE: Optional[Dict[CrudMethods, RequestResponseModel]]
    PRIMARY_KEY_NAME: Optional[str]
    UNIQUE_LIST: Optional[List[str]]

    def get_available_request_method(self):
        return [i for i in self.dict(exclude_unset=True, ).keys() if i in ["GET", "POST", "PUT", "PATCH", "DELETE"]]

    def get_model_by_request_method(self, request_method):
        available_methods = self.dict()
        if request_method not in available_methods.keys():
            raise InvalidRequestMethod(f'{request_method} is not an available request method')
        if not available_methods[request_method]:
            raise RequestMissing(
                f'{request_method} is not available, '
                f'make sure the CRUDModel contains this request method')
        _ = available_methods[request_method]
        return _

