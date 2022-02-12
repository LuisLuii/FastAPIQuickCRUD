import json
import os
from collections import OrderedDict

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from src.fastapi_quickcrud import CrudMethods
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from tests.test_implementations.test_sqlalchemy.api_test_async import  app, UntitledTable256


TEST_DATABASE_URL = os.environ.get('TEST_DATABASE_ASYNC_URL',
                                   'postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres')
engine = create_async_engine(TEST_DATABASE_URL, echo=True, future=True)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session



UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.UPSERT_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_one = crud_router_builder(db_session=get_session,
                                      db_model=UntitledTable256,
                                      crud_models=UntitledTable256Model,
                                      prefix="/test_creation_one",
                                      async_mode=True,
                                      tags=["test"]
                                      )
UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.UPSERT_MANY,
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_many = crud_router_builder(db_session=get_session,
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       prefix="/test_creation_many",
                                       async_mode=True,
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

test_post_and_redirect_get = crud_router_builder(db_session=get_session,
                                                 db_model=UntitledTable256,
                                                 crud_models=UntitledTable256Model,
                                                 prefix="/test_post_direct_get",
                                                 async_mode=True,
                                                 tags=["test"]
                                                 )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.FIND_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
test_get_data = crud_router_builder(db_session=get_session,
                                    db_model=UntitledTable256,
                                    crud_models=UntitledTable256Model,
                                    prefix="/test",
                                    async_mode=True,
                                    tags=["test"]
                                    )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.UPDATE_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])
test_update_data = crud_router_builder(db_session=get_session,
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       async_mode=True,
                                       prefix="/test_update_one",
                                       tags=["test"]
                                       )
[app.include_router(i) for i in
 [test_post_and_redirect_get, test_update_data, test_create_one, test_create_many, test_get_data]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


def test_create_one_and_update_one():
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

    primary_key, = [i[primary_key_name] for i in insert_response_data]
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
    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24", "float4_value": 10.50,
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "int8_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00",
                   "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afb6", "varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    response = client.put(f'/test_update_one/{primary_key}?{query_string}', data=json.dumps(update_data))
    response_data = response.json()
    assert response_data
    for i in update_data:
        print(i)
        print(response_data[i])
        assert response_data[i] == update_data[i]


def test_create_one_and_update_one_but_not_found():
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
              "time_valuez____from": '18:18:18+00:00',
              "time_valuez____to": '18:18:18+00:00',
              "time_valuez____list": '18:18:18+00:00',
              "varchar_value____str": 'string',
              "varchar_value____str_____matching_pattern": 'case_sensitive',
              "varchar_value____list": 'string',
              }
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    update_data = {"bool_value": False, "char_value": "string_u  ", "date_value": "2022-07-24", "float4_value": 10.50,
                   "float8_value": 10.5, "int2_value": 10, "int4_value": 10, "int8_value": 10, "interval_value": 3600,
                   "json_value": {'test': 'hello'}, "jsonb_value": {'test': 'hello'}, "numeric_value": 10,
                   "text_value": "string_update",
                   "timestamp_value": "2022-07-24T02:54:53.285000",
                   "timestamptz_value": "2022-07-24T02:54:53.285000+00:00",
                   "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afb6", "varchar_value": "string",
                   "array_value": [1, 2, 3, 4, 5],
                   "array_str__value": ["test"], "time_value": "18:19:18", "timetz_value": "18:19:18+00:00"}
    response = client.put(f'/test_update_one/{primary_key}?{query_string}', data=json.dumps(update_data))
    # response_data = response.json()
    response.status_code = 404
    # assert response_data
    # for i in update_data:
    #     assert response_data[i] == update_data[i]

