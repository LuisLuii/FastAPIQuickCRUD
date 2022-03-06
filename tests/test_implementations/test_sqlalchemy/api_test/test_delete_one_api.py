import json
from collections import OrderedDict

from starlette.testclient import TestClient

from src.fastapi_quickcrud.crud_router import crud_router_builder
from src.fastapi_quickcrud.misc.type import CrudMethods
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from tests.test_implementations.test_sqlalchemy.api_test import get_transaction_session, app, UntitledTable256


UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.UPSERT_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
# Model Test
# api_model = UntitledTable256Model.__dict__['POST']
# assert api_model
# create_one_model = api_model[CrudMethods.UPSERT_ONE].__dict__
# assert create_one_model['requestModel'] or create_one_model['responseModel']
# create_one_request_model = deepcopy(create_one_model['requestModel'].__dict__['__fields__'])
# create_one_response_model = deepcopy(create_one_model['responseModel'].__dict__['__fields__'])
# Request Test
# assert create_one_request_model.pop('on_conflict', False)
# for k, v in create_one_request_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")

# Response Test
# for k, v in create_one_response_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")

test_create_one = crud_router_builder(db_session=get_transaction_session,
                                      db_model=UntitledTable256,
                                      crud_models=UntitledTable256Model,
                                      prefix="/test_creation_one",
                                      tags=["test"]
                                      )
UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.UPSERT_MANY,
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
# # Model Test
# api_model = UntitledTable256Model.__dict__['POST']
# assert api_model
# create_many_model = api_model[CrudMethods.UPSERT_MANY].__dict__
# assert create_many_model['requestModel'] or create_many_model['responseModel']
# create_many_request_model = deepcopy(create_many_model['requestModel'].__dict__['__fields__'])
# create_many_response_model = deepcopy(create_many_model['responseModel'].__dict__['__fields__'])
#
# # Request Model Test
# assert create_many_request_model.pop('on_conflict', None)
# insert_many_model = create_many_request_model['insert'].sub_fields[0].outer_type_.__dict__['__fields__']
# for k, v in insert_many_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")
#
# # Response Model Test
# for k, v in create_many_response_model.items():
#     create_many_response_model_item = v.type_.__dict__['__fields__']
#     for k, v in create_many_response_model_item.items():
#         sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#         if sql_schema.server_default or sql_schema.default:
#             assert not v.required
#         elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#             assert not v.required
#         elif sql_schema.nullable:
#             assert not v.required
#         elif not sql_schema.nullable:
#             assert v.required
#         elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#             assert v.required
#         else:
#             print(f"{v.name=}")
#             print(f"{v.required=}")
#             print(f"{v.default=}")

test_create_many = crud_router_builder(db_session=get_transaction_session,
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       prefix="/test_creation_many",
                                       tags=["test"]
                                       )

# Response Mode Test
# response_many = create_many_response_model['__root__'].sub_fields[0].outer_type_.__dict__['__fields__']
# for k, v in response_many.items():
#     assert not v.required

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.POST_REDIRECT_GET
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
# Model Test
# api_model = UntitledTable256Model.__dict__['POST']
# assert api_model
# post_redirect_get_model = api_model[CrudMethods.POST_REDIRECT_GET].__dict__
# assert post_redirect_get_model['requestModel'] or post_redirect_get_model['responseModel']
# post_redirect_get_request_model = deepcopy(post_redirect_get_model['requestModel'].__dict__['__fields__'])
# post_redirect_get_response_model = deepcopy(post_redirect_get_model['responseModel'].__dict__['__fields__'])

# Request Model Test

# for k, v in post_redirect_get_request_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")

# Response Model Test
# for k, v in post_redirect_get_response_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")

# for k, v in post_redirect_get_response_model.items():
#     assert v.required

test_post_and_redirect_get = crud_router_builder(db_session=get_transaction_session,
                                                 db_model=UntitledTable256,
                                                 crud_models=UntitledTable256Model,
                                                 prefix="/test_post_direct_get",
                                                 tags=["test"]
                                                 )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.FIND_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
# # # Model Test
# api_model = UntitledTable256Model.__dict__['GET']
# assert api_model
# get_one_model = api_model[CrudMethods.FIND_ONE].__dict__
# assert get_one_model['requestModel'] or get_one_model['responseModel']
# get_one_request_model = deepcopy(get_one_model['requestModel'].__dict__['__fields__'])
# get_one_response_model = deepcopy(get_one_model['responseModel'].__dict__['__fields__'])
# primary_key_of_get_sql_schema = get_one_request_model[UntitledTable256.__dict__['primary_key_of_table']]
# assert not primary_key_of_get_sql_schema.required
# get_one_request_model.pop(UntitledTable256.__dict__['primary_key_of_table'], None)
# for k, v in get_one_request_model.items():
#     assert not v.required
# # FIXME some thing may not require
# for k, v in get_one_response_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")
test_get_data = crud_router_builder(db_session=get_transaction_session,
                                    db_model=UntitledTable256,
                                    crud_models=UntitledTable256Model,
                                    prefix="/test",
                                    tags=["test"]
                                    )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.DELETE_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
# # # Model Test
# api_model = UntitledTable256Model.__dict__['GET']
# assert api_model
# get_one_model = api_model[CrudMethods.FIND_ONE].__dict__
# assert get_one_model['requestModel'] or get_one_model['responseModel']
# get_one_request_model = deepcopy(get_one_model['requestModel'].__dict__['__fields__'])
# get_one_response_model = deepcopy(get_one_model['responseModel'].__dict__['__fields__'])
# primary_key_of_get_sql_schema = get_one_request_model[UntitledTable256.__dict__['primary_key_of_table']]
# assert not primary_key_of_get_sql_schema.required
# get_one_request_model.pop(UntitledTable256.__dict__['primary_key_of_table'], None)
# for k, v in get_one_request_model.items():
#     assert not v.required
# # FIXME some thing may not require
# for k, v in get_one_response_model.items():
#     sql_schema = UntitledTable256.__dict__[v.name].comparator
#
#     if sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif not sql_schema.nullable and sql_schema.server_default or sql_schema.default:
#         assert not v.required
#     elif sql_schema.nullable:
#         assert not v.required
#     elif not sql_schema.nullable:
#         assert v.required
#     elif not sql_schema.nullable and not sql_schema.server_default or not sql_schema.default:
#         assert v.required
#     else:
#         print(f"{v.name=}")
#         print(f"{v.required=}")
#         print(f"{v.default=}")
test_delete_data = crud_router_builder(db_session=get_transaction_session,
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       prefix="/test_delete_one",
                                       tags=["test"]
                                       )
[app.include_router(i) for i in
 [test_post_and_redirect_get, test_delete_data, test_create_one, test_create_many, test_get_data]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


def test_create_one_and_delete_one():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [
                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285Z",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                        "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key ,= [i[primary_key_name] for i in insert_response_data]
    params = {"bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 2,
              "float4_value____list": 0,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '18:18:18',
              "time_value____to": '18:18:18',
              "time_value____list": '18:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "uuid_value_value____list": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
              "time_value____from": '18:18:18+00:00',
              "time_value____to": '18:18:18+00:00',
              "time_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    update_data = {"bool_value": False}
    response = client.delete(f'/test_delete_one/{primary_key}?{query_string}')
    response_data = response.json()
    assert response.status_code == 200
    assert response.headers['x-total-count'] == '1'



def test_create_one_and_delete_one_but_not_found():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [
                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                        "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key ,= [i[primary_key_name] for i in insert_response_data]
    params = {"bool_value____list": True,
              "char_value____str": 'string%',
              "char_value____str_____matching_pattern": 'case_sensitive',
              "date_value____from": "2021-07-22",
              "date_value____to": "2021-07-25",
              "float4_value____from": -1,
              "float4_value____to": 2,
              "float4_value____list": 0,
              "float8_value____from": -1,
              "float8_value____to": 2,
              "float8_value____list": 0,
              "int2_value____from": -1,
              "int2_value____to": 9,
              "int2_value____list": 0,
              "int4_value____from": -1,
              "int4_value____to": 9,
              "int4_value____list": 0,
              "int8_value____from": -1,
              "int8_value____to": 9,
              "int8_value____list": 0,
              "interval_value____from": -1,
              "interval_value____to": 9,
              "interval_value____list": 0,
              "numeric_value____from": -1,
              "numeric_value____to": 9,
              "numeric_value____list": 0,
              "text_value____list": "string",
              "time_value____from": '10:18:18',
              "time_value____to": '12:18:18',
              "time_value____list": '10:18:18',
              "timestamp_value_value____from": "2021-07-24T02:54:53.285",
              "timestamp_value_value____to": "2021-07-24T02:54:53.285",
              "timestamp_value_value____list": "2021-07-24T02:54:53.285",
              "timestamptz_value_value____from": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____to": "2021-07-24T02:54:53.285Z",
              "timestamptz_value_value____list": "2021-07-24T02:54:53.285Z",
              "uuid_value_value____list": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
              "timez_value____from": '18:18:18+00:00',
              "timez_value____to": '18:18:18+00:00',
              "timez_value____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    update_data = {"bool_value": False}
    response = client.delete(f'/test_delete_one/{primary_key}?{query_string}')
    assert response.status_code == 404



def test_create_one_and_delete_one_but_not_found_test_case_sensitive():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"insert": [
                       {"bool_value": True, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0,
                        "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0,
                        "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string",
                        "timestamp_value": "2021-07-24T02:54:53.285",
                        "timestamptz_value": "2021-07-24T02:54:53.285Z",
                        "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string",
                        "array_value": [0], "array_str__value": ["string"], "time_value": "18:18:18",
                        "timetz_value": "18:18:18+00:00"},
                       ]}

    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    insert_response_data = response.json()

    primary_key ,= [i[primary_key_name] for i in insert_response_data]
    params = {
              "varchar_value____str": 'String',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              }
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    update_data = {"bool_value": False}
    response = client.delete(f'/test_delete_one/{primary_key}?{query_string}')
    assert response.status_code == 404


    params = {
              "varchar_value____str": 'String',
              "varchar_value____str_____matching_pattern": 'case_insensitive',
              }
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    update_data = {"bool_value": False}
    response = client.delete(f'/test_delete_one/{primary_key}?{query_string}')
    assert response.status_code == 200

