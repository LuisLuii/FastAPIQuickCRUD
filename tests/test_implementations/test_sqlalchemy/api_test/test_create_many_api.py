import json
import uuid
from datetime import date, timedelta, datetime, timezone

from starlette.testclient import TestClient

from src.fastapi_quickcrud import CrudMethods
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from src.fastapi_quickcrud.misc.exceptions import ConflictColumnsCannotHit
from tests.test_implementations.test_sqlalchemy.api_test import get_transaction_session, app, UntitledTable256



# Create Many API Test

test_create_many = crud_router_builder(db_session=get_transaction_session,
                                       db_model=UntitledTable256,
                                       prefix="/test_creation_many",
                                       crud_methods=[
                                           CrudMethods.UPSERT_MANY,
                                       ],
                                       exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
                                       tags=["test"]
                                       )
[app.include_router(i) for i in [test_create_many]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


def create_example_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = '{ "insert": [ { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z", "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] }, { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z", "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] }, { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z", "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] } ] }'

    response = client.post('/test_creation_many', headers=headers, data=data)
    assert response.status_code == 201
    return response.json()


def test_try_only_input_required_fields():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = '{ "insert": [ { "float4_value": 1, "int2_value": 1, "int4_value": 1 },{ "float4_value": 2, "int2_value": 2, "int4_value": 2 },{ "float4_value": 3, "int2_value": 3, "int4_value": 3 } ] }'
    data_ = json.loads(data)['insert']
    response = client.post('/test_creation_many', headers=headers, data=data)
    assert response.status_code == 201
    response_result = response.json()
    for index, value in enumerate(data_):
        res_result_by_index = response_result[index]
        for k, v in value.items():
            assert res_result_by_index[k] == v


def test_try_input_with_conflict_but_conflict_columns_not_hit():
    sample_data = create_example_data()
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"on_conflict": {"update_columns": ["bool_value", "float8_value", "varchar_value", "interval_value",
                                               "time_value", "int8_value", "jsonb_value", "timetz_value",
                                               "array_str__value", "text_value", "char_value", "uuid_value",
                                               "array_value", "numeric_value", "timestamp_value", "int2_value",
                                               "date_value", "json_value", "timestamptz_value"]}}
    insert_data = []
    for i in sample_data:
        _ = {}
        for k, v in i.items():
            _[k] = v
        for k, v in {"float4_value": 99, "int2_value": 99, "int4_value": 99}.items():
            _[k] = v
        insert_data.append(_)
    data['insert'] = insert_data

    try:
        _ = json.dumps(data)
        response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    except ConflictColumnsCannotHit as e:
        pass
    assert response.status_code == 409


def test_try_input_with_conflict():
    sample_data = create_example_data()
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"on_conflict": {"update_columns": ["bool_value", "float8_value", "varchar_value", "interval_value",
                                               "time_value", "int8_value", "jsonb_value", "timetz_value",
                                               "array_str__value", "text_value", "char_value", "uuid_value",
                                               "array_value", "numeric_value", "timestamp_value", "int2_value",
                                               "date_value", "json_value", "timestamptz_value"]}}
    insert_data = []
    for i in sample_data:
        _ = {}
        for k, v in i.items():
            _[k] = v
        for k, v in {"float8_value": 0.7}.items():
            _[k] = v
        insert_data.append(_)
    data['insert'] = insert_data
    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    response_result = response.json()
    for index, value in enumerate(data['insert']):
        res_result_by_index = response_result[index]
        for k, v in value.items():
            assert res_result_by_index[k] == value[k]


def test_try_input_without_conflict():
    sample_data = create_example_data()

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {}
    insert_data = []
    for i in sample_data:
        _ = {}
        for k, v in i.items():
            _[k] = v
        for k, v in {"float4_value": 99, "int2_value": 99, "int4_value": 99}.items():
            _[k] = v
        insert_data.append(_)
    data['insert'] = insert_data
    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 409


def test_update_specific_columns_when_conflict():
    def update_all_fields():
        headers = {
            'accept': 'application/json',
        }
        response_data = create_example_data()

        # create the data
        update_column_on_conflict = {
            "update_columns": [
                "int8_value",
                "numeric_value",
                "varchar_value",
                "json_value",
                "float8_value",
                "time_value",
                "timestamp_value",
                "timestamptz_value",
                "array_value",
                "bool_value",
                "array_str__value",
                "int2_value",
                "text_value",
                "uuid_value",
                "char_value",
                "jsonb_value",
                "interval_value",
                "date_value",
                "timetz_value"
            ]
        }
        tmp = {}
        tmp['on_conflict'] = update_column_on_conflict
        bool_value_change = not response_data[0]['bool_value']
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
        change = {}

        change['bool_value'] = bool_value_change
        change['char_value'] = char_value_change
        change['date_value'] = date_value_change
        change['float8_value'] = float8_value_change
        change['int2_value'] = int2_value_change
        change['int8_value'] = int8_value_change
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
        for i in response_data:
            for k, v in change.items():
                i[k] = v
        tmp['insert'] = response_data
        response = client.post('/test_creation_many', headers=headers, data=json.dumps(tmp))
        assert response.status_code == 201
        response_result = response.json()
        for i in response_result:
            for k, v in i.items():
                if k in change:
                    if isinstance(v, str):
                        v = v.strip()

                    assert json.dumps(change[k]).strip() == json.dumps(v).strip()

    def update_partial_fields_1():
        headers = {
            'accept': 'application/json',
        }
        response_data = create_example_data()

        # create the data
        update_column_on_conflict = {
            "update_columns": [
                "int8_value",
                "numeric_value",
                "varchar_value",
                "json_value",
                "float8_value",
                "time_value",
                "timestamp_value",
                "timestamptz_value",
                "array_value",
                "bool_value",
                "array_str__value",
            ]
        }
        tmp = {}
        tmp['on_conflict'] = update_column_on_conflict
        bool_value_change = not response_data[0]['bool_value']
        float8_value_change = 0.1
        int8_value_change = 100
        json_value_change = {"hello": "world"}
        numeric_value_change = 19
        time_value_change = '18:18:18'
        timestamp_value_change = str(datetime.utcnow().isoformat())
        timestamptz_value_change = str(datetime.utcnow().replace(tzinfo=timezone.utc).isoformat())
        uuid_value_change = str(uuid.uuid4())
        varchar_value_change = 'hello world'
        array_value_change = [1, 2, 3, 4]
        array_str__value_change = ['1', '2', '3', '4']
        change = {}
        change['int8_value'] = int8_value_change
        change['numeric_value'] = numeric_value_change
        change['varchar_value'] = varchar_value_change
        change['json_value'] = json_value_change
        change['float8_value'] = float8_value_change
        change['time_value'] = time_value_change
        change['timestamp_value'] = timestamp_value_change
        change['timestamptz_value'] = timestamptz_value_change
        change['array_value'] = array_value_change
        change['bool_value'] = bool_value_change
        change['array_str__value'] = array_str__value_change

        for i in response_data:
            for k, v in change.items():
                i[k] = v
        tmp['insert'] = response_data
        response = client.post('/test_creation_many', headers=headers, data=json.dumps(tmp))
        assert response.status_code == 201
        response_result = response.json()
        for i in response_result:
            for k, v in i.items():
                if k in change:
                    if isinstance(v, str):
                        v = v.strip()

                    assert json.dumps(change[k]).strip() == json.dumps(v).strip()

    def update_partial_fields_2():
        headers = {
            'accept': 'application/json',
        }
        response_data = create_example_data()

        # create the data
        update_column_on_conflict = {
            "update_columns": [

                "int2_value",
                "text_value",
                "uuid_value",
                "char_value",
                "jsonb_value",
                "interval_value",
                "date_value",
                "timetz_value"
            ]
        }
        tmp = {}
        tmp['on_conflict'] = update_column_on_conflict
        char_value_change = "test"
        date_value_change = str(date.today() - timedelta(days=1))
        int2_value_change = 100
        interval_value_change = float(5400)
        jsonb_value_change = {"hello": "world"}
        text_value_change = 'hello world'
        timetz_value_change = '18:18:18+00:00'
        uuid_value_change = str(uuid.uuid4())
        change = {}
        change['int2_value'] = int2_value_change
        change['text_value'] = text_value_change
        change['uuid_value'] = uuid_value_change
        change['char_value'] = char_value_change
        change['jsonb_value'] = jsonb_value_change
        change['interval_value'] = interval_value_change
        change['date_value'] = date_value_change
        change['timetz_value'] = timetz_value_change

        for i in response_data:
            for k, v in change.items():
                i[k] = v
        tmp['insert'] = response_data
        response = client.post('/test_creation_many', headers=headers, data=json.dumps(tmp))
        assert response.status_code == 201
        response_result = response.json()
        for i in response_result:
            for k, v in i.items():
                if k in change:
                    if isinstance(v, str):
                        v = v.strip()

                    assert json.dumps(change[k]).strip() == json.dumps(v).strip()

    update_all_fields()
    update_partial_fields_1()
    update_partial_fields_2()
