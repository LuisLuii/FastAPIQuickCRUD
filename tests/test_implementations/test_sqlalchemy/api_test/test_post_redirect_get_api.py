import json
import uuid
from datetime import date, timedelta, datetime, timezone
from http import HTTPStatus

from starlette.testclient import TestClient

from src.fastapi_quickcrud import CrudMethods
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from tests.test_implementations.test_sqlalchemy.api_test import get_transaction_session, app, UntitledTable256

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
# # Model Test
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
                                    prefix="/test_post_direct_get",
                                    tags=["test"]
                                    )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.POST_REDIRECT_GET
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_post_and_redirect_get_without_get = crud_router_builder(db_session=get_transaction_session,
                                                             db_model=UntitledTable256,
                                                             crud_models=UntitledTable256Model,
                                                             prefix="/test_post_direct_get_without_get",
                                                             tags=["test"]
                                                             )
[app.include_router(i) for i in [test_post_and_redirect_get, test_get_data, test_post_and_redirect_get_without_get]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


# Post Redirect Get API Test

def test_create_one_but_no_follow_redirect():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    data = '{ "bool_value": true, "char_value": "string", "date_value": "2021-07-24", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-24T02:54:53.285Z", "timestamptz_value": "2021-07-24T02:54:53.285Z", "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] }'

    response = client.post('/test_post_direct_get', headers=headers, data=data, allow_redirects=False)
    assert response.status_code == HTTPStatus.SEE_OTHER


def test_create_one_with_redirect():
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    change = {}

    bool_value_change = False
    char_value_change = "test"
    date_value_change = str(date.today() - timedelta(days=1))
    float8_value_change = 0.1
    int2_value_change = 100
    int8_value_change = 100
    interval_value_change = float(5400)
    json_value_change = {"hello": "world"}
    jsonb_value_change = {"hello": "world"}
    numeric_value_change = 19
    text_value_change = 'hello world'
    time_value_change = '18:18:18'
    timestamp_value_change = str(datetime.utcnow().isoformat())
    timestamptz_value_change = str(datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
    timetz_value_change = '18:18:18+00:00'
    uuid_value_change = str(uuid.uuid4())
    varchar_value_change = 'hello world'
    array_value_change = [1, 2, 3, 4]
    array_str__value_change = ['1', '2', '3', '4']

    change['bool_value'] = bool_value_change
    change['char_value'] = char_value_change
    change['date_value'] = date_value_change
    change['float8_value'] = float8_value_change
    change['int2_value'] = int2_value_change
    change['int8_value'] = int8_value_change
    change['float4_value'] = 0.4
    change['int4_value'] = 4
    change['interval_value'] = interval_value_change
    change['json_value'] = json_value_change
    change['jsonb_value'] = jsonb_value_change
    change['numeric_value'] = numeric_value_change
    change['text_value'] = text_value_change
    change['time_value'] = time_value_change
    change['timestamp_value'] = timestamp_value_change
    change['timestamptz_value'] = timestamptz_value_change
    change['timetz_value'] = timetz_value_change
    change['uuid_value'] = uuid_value_change
    change['varchar_value'] = varchar_value_change
    change['array_value'] = array_value_change
    change['array_str__value'] = array_str__value_change
    data_ = json.dumps(change)
    response = client.post('/test_post_direct_get', headers=headers, data=data_, allow_redirects=True)
    assert response.status_code == HTTPStatus.OK
    response_data = response.json()
    assert primary_key_name in response_data
    for k, v in response_data.items():
        if k in change:
            if isinstance(v, str):
                v = v.strip()
            response_ = json.dumps(v).strip()
            request_ = json.dumps(change[k]).strip()
            assert request_ == response_
    return response_data


def test_create_but_conflict():
    data = test_create_one_with_redirect()

    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.post('/test_post_direct_get', headers=headers, data=json.dumps(data), allow_redirects=True)
    assert response.status_code == HTTPStatus.CONFLICT


def test_create_but_not_found_get_api():
    change = {}

    bool_value_change = False
    char_value_change = "test"
    date_value_change = str(date.today() - timedelta(days=1))
    float8_value_change = 0.1
    int2_value_change = 100
    int8_value_change = 100
    interval_value_change = float(5400)
    json_value_change = {"hello": "world"}
    jsonb_value_change = {"hello": "world"}
    numeric_value_change = 19
    text_value_change = 'hello world'
    time_value_change = '18:18:18'
    timestamp_value_change = str(datetime.utcnow().isoformat())
    timestamptz_value_change = str(datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
    timetz_value_change = '18:18:18+00:00'
    uuid_value_change = str(uuid.uuid4())
    varchar_value_change = 'hello world'
    array_value_change = [1, 2, 3, 4]
    array_str__value_change = ['1', '2', '3', '4']

    change['bool_value'] = bool_value_change
    change['char_value'] = char_value_change
    change['date_value'] = date_value_change
    change['float8_value'] = float8_value_change
    change['int2_value'] = int2_value_change
    change['int8_value'] = int8_value_change
    change['float4_value'] = 0.4
    change['int4_value'] = 4
    change['interval_value'] = interval_value_change
    change['json_value'] = json_value_change
    change['jsonb_value'] = jsonb_value_change
    change['numeric_value'] = numeric_value_change
    change['text_value'] = text_value_change
    change['time_value'] = time_value_change
    change['timestamp_value'] = timestamp_value_change
    change['timestamptz_value'] = timestamptz_value_change
    change['timetz_value'] = timetz_value_change
    change['uuid_value'] = uuid_value_change
    change['varchar_value'] = varchar_value_change
    change['array_value'] = array_value_change
    change['array_str__value'] = array_str__value_change
    data = json.dumps(change)
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

    response = client.post('/test_post_direct_get_without_get', headers=headers, data=data, allow_redirects=True)
    assert response.status_code == HTTPStatus.NOT_FOUND


