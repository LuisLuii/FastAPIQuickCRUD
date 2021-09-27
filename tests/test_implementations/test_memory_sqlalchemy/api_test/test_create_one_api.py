import json
import random
import uuid
from datetime import date, timedelta, datetime, timezone

from starlette.testclient import TestClient

from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from src.fastapi_quickcrud.crud_router import crud_router_builder
from src.fastapi_quickcrud.misc.exceptions import ConflictColumnsCannotHit, UnknownColumn, UpdateColumnEmptyException
from src.fastapi_quickcrud.misc.type import CrudMethods
from tests.test_implementations.test_memory_sqlalchemy.api_test import  app, UntitledTable256

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.CREATE_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_one = crud_router_builder(
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

test_create_many = crud_router_builder(
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       prefix="/test_creation_many",
                                       tags=["test"]
                                       )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.POST_REDIRECT_GET
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_post_and_redirect_get = crud_router_builder(
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

test_get_data = crud_router_builder(
                                    db_model=UntitledTable256,
                                    crud_models=UntitledTable256Model,
                                    prefix="/test",
                                    tags=["test"]
                                    )
[app.include_router(i) for i in [test_post_and_redirect_get, test_create_one, test_create_many, test_get_data]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


# Create One API Test

def create_example_data():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = '{"float4_value": 0, "int2_value": 0, "int4_value": 0 }'

    response = client.post('/test_creation_one', headers=headers, data=data)
    assert response.status_code == 201
    return response.json()


def test_try_only_input_required_fields():
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    data = {"float4_value": 0.0, "int2_value": 0, "int4_value": 0}

    response = client.post('/test_creation_one', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    response_result = response.json()
    for k, v in data.items():
        assert response_result[k] == v


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
    for k, v in sample_data.items():
        data[k] = v
    for k, v in {"float4_value": 99, "int2_value": 99, "int4_value": 99}.items():
        data[k] = v
    # for k, v in {"float4_value": 99.9, "int2_value": 99, "int4_value": 99}.items():
    #     data[k] = v
    try:
        _ = json.dumps(data)
        response = client.post('/test_creation_one', headers=headers, data=json.dumps(data))
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
    for k, v in sample_data.items():
        data[k] = v
    for k, v in {"float4_value": 0.0, "int2_value": 99, "int4_value": 0}.items():
        data[k] = v
    response = client.post('/test_creation_one', headers=headers, data=json.dumps(data))
    assert response.status_code == 409


def test_try_input_without_conflict():
    sample_data = create_example_data()

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {}
    for k, v in sample_data.items():
        data[k] = v
    for k, v in {"float4_value": 0.0, "int2_value": 99, "int4_value": 0}.items():
        data[k] = v
    # data['on_conflict'] = {'update_columns': []}

    response = client.post('/test_creation_one', headers=headers, data=json.dumps(data))
    assert response.status_code == 409



