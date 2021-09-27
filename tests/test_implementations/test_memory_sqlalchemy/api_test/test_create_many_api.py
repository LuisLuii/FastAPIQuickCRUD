import json

from starlette.testclient import TestClient

from src.fastapi_quickcrud import CrudMethods
from src.fastapi_quickcrud import crud_router_builder
from src.fastapi_quickcrud.misc.exceptions import ConflictColumnsCannotHit
from tests.test_implementations.test_memory_sqlalchemy.api_test import UntitledTable256, app

# Create Many API Test

test_create_many = crud_router_builder(crud_methods=[CrudMethods.CREATE_MANY,
                                                     ],
                                       exclude_columns=['bytea_value', 'xml_value', 'box_valaue'],
                                       db_model=UntitledTable256,
                                       prefix="/test_creation_many",
                                       tags=["test"],
                                       autocommit=True
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

    data = '[ { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z", "varchar_value": "string"}, { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z",  "varchar_value": "string"}, { "bool_value": true, "char_value": "string", "date_value": "2021-07-23", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0,  "numeric_value": 0, "text_value": "string", "timestamp_value": "2021-07-23T02:38:24.963Z", "timestamptz_value": "2021-07-23T02:38:24.963Z",  "varchar_value": "string"} ]'

    response = client.post('/test_creation_many', headers=headers, data=data)
    assert response.status_code == 201
    return response.json()


def test_try_only_input_required_fields():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = '[ { "float4_value": 1, "int2_value": 1, "int4_value": 1 },{ "float4_value": 2, "int2_value": 2, "int4_value": 2 },{ "float4_value": 3, "int2_value": 3, "int4_value": 3 } ] '
    data_ = json.loads(data)
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

    insert_data = []
    for i in sample_data:
        _ = {}
        for k, v in {"float4_value": 99, "int2_value": 99, "int4_value": 99}.items():
            _[k] = v
        insert_data.append(_)
    data = insert_data

    try:
        _ = json.dumps(data)
        response = client.post('/test_creation_many', headers=headers, data=json.dumps(sample_data))
    except ConflictColumnsCannotHit as e:
        pass
    assert response.status_code == 409


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
    response = client.post('/test_creation_many', headers=headers, data=json.dumps(insert_data))
    assert response.status_code == 409
