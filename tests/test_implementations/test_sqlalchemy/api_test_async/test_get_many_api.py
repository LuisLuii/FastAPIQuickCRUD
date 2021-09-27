import json
from collections import OrderedDict
from urllib.parse import urlencode

from starlette.testclient import TestClient

from src.fastapi_quickcrud.misc.exceptions import UnknownOrderType, UnknownColumn
from src.fastapi_quickcrud.crud_router import crud_router_builder
from src.fastapi_quickcrud.misc.type import CrudMethods
from src.fastapi_quickcrud.misc.utils import sqlalchemy_to_pydantic
from tests.test_implementations.test_sqlalchemy.api_test_async import get_transaction_session, app, UntitledTable256


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

# Create Many API Test

test_create_many = crud_router_builder(db_session=get_transaction_session,
                                       db_model=UntitledTable256,
                                       crud_models=UntitledTable256Model,
                                       prefix="/test_creation_many",
                                       async_mode=True,
                                       tags=["test"]
                                       )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.FIND_MANY,
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_find_many = crud_router_builder(db_session=get_transaction_session,
                                     db_model=UntitledTable256,
                                     crud_models=UntitledTable256Model,
                                     prefix="/test_get_many",
                                     async_mode=True,
                                     tags=["test"]
                                     )

[app.include_router(i) for i in [test_create_many, test_find_many]]

client = TestClient(app)

primary_key_name = UntitledTable256.primary_key_of_table
unique_fields = UntitledTable256.unique_fields


# test create many

def create_example_data(num=1, **kwargs):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    insert_sample_item = {"bool_value": kwargs.get('bool_value', True),
                          "char_value": kwargs.get('char_value', 'string'),
                          "date_value": kwargs.get('date_value', "2021-07-23"),
                          "float4_value": kwargs.get('float4_value', 0.6),
                          "float8_value": kwargs.get('float8_value', 0.8),
                          "int2_value": kwargs.get('int2_value', 11),
                          "int4_value": kwargs.get('int4_value', 1),
                          "int8_value": kwargs.get('int8_value', 3),
                          "interval_value": kwargs.get('interval_value', 5),
                          "json_value": kwargs.get('json_value', {}),
                          "jsonb_value": kwargs.get('jsonb_value', {}),
                          "numeric_value": kwargs.get('numeric_value', 110),
                          "text_value": kwargs.get('text_value', 'string'),
                          "timestamp_value": kwargs.get('timestamp_value', "2021-07-23T02:38:24.963"),
                          "timestamptz_value": kwargs.get('timestamptz_value', "2021-07-23T02:38:24.963Z"),
                          "uuid_value": kwargs.get('uuid_value', "3fa85f64-5717-4562-b3fc-2c963f66afa6"),
                          "varchar_value": kwargs.get('varchar_value', 'string'),
                          "array_value": kwargs.get('array_value', [1, 2, 3, 4]),
                          "array_str__value": kwargs.get('array_str__value', ["string", "string1"])}
    data = {'insert': [insert_sample_item for i in range(num)]}

    response = client.post('/test_creation_many', headers=headers, data=json.dumps(data))
    assert response.status_code == 201
    response_result = response.json()
    for i in response_result:
        assert primary_key_name in i
        assert i[primary_key_name]
    return response_result


# test pagination by offset and limit and ordering
def test_pagination_and_ording():
    sample_data = create_example_data(5 * 10)
    assert len(sample_data) == 5 * 10
    limit = 5
    seem = []
    for num in range(0, 5 * 10, 5):
        response = client.get(
            f'/test_get_many?limit={limit}&offset={num}&order_by_columns=primary_key%20%3A%20DESC%20')
        response.headers['x-total-count'] == limit
        assert response.status_code == 200
        _ = response.json()
        for i in _:
            assert i not in seem
            seem.append(i)
            assert i in sample_data


# test create a new data and get by primary key
def test_create_new_data_and_get_by_primary_key():
    sample_data = create_example_data(10)
    primary_key_list = [i[primary_key_name] for i in sample_data]
    min_key = min(primary_key_list)
    max_key = max(primary_key_list)
    params = {"primary_key____from": min_key, "primary_key____to": max_key}
    from urllib.parse import urlencode
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 10
    for i in response_data:
        assert i['primary_key'] in primary_key_list

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "primary_key____from_____comparison_operator": 'Greater_than',
              "primary_key____to_____comparison_operator": 'Less_than'}

    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 8
    for i in response_data:
        assert i['primary_key'] in primary_key_list


# test create a more than one data which value is TRUE of boolean type, and get many
def test_create_a_more_than_one_data_which_value_is_TRUE_of_boolean_type_and_get_many():
    bool_false_sample_data = create_example_data(5, bool_value=False)
    bool_true_sample_data = create_example_data(5, bool_value=True)
    primary_key_list = [i[primary_key_name] for i in bool_false_sample_data] + \
                       [i[primary_key_name] for i in bool_true_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)
    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "In",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params)) + f"&bool_value____list=False"

    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 10

    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "In",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i not in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()
    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "In",
              "bool_value____list": False}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i not in response.json()

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Equal",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params)) + f"&bool_value____list=False"

    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 10

    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Equal",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i not in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()
    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Equal",
              "bool_value____list": False}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i not in response.json()

    #

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_in",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params)) + f"&bool_value____list=False"

    response = client.get(f'/test_get_many?{query_string}')
    response.status_code = 204

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_in",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i not in response.json()
    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_in",
              "bool_value____list": False}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i not in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_equal",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params)) + f"&bool_value____list=False"

    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 10

    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()

    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_equal",
              "bool_value____list": True}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i in response.json()
    for i in bool_true_sample_data:
        assert i not in response.json()
    params = {"primary_key____from": min_key,
              "primary_key____to": max_key,
              "bool_value____list_____comparison_operator": "Not_equal",
              "bool_value____list": False}
    query_string = urlencode(OrderedDict(**params))
    response = client.get(f'/test_get_many?{query_string}')
    response_data = response.json()
    assert len(response_data) == 5
    for i in bool_false_sample_data:
        assert i not in response.json()
    for i in bool_true_sample_data:
        assert i in response.json()


# test create a more than one data of char/text/varchar type, and get many
def test_create_a_more_than_one_data_and_get_many_1():
    char_str_sample_data = create_example_data(5, char_value='string')
    char_test_sample_data = create_example_data(5, char_value='test')
    primary_key_list = [i[primary_key_name] for i in char_str_sample_data] + \
                       [i[primary_key_name] for i in char_test_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)

    # match_regex_with_case_sensitive/ dose not match_regex_with_case_sensitive
    def match_regex_with_case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "char_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_match_regex_with_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "char_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "char_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def match_regex_with_case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "char_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "char_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # does_not_match_regex_with_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "char_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "char_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "char_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "char_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'case_sensitive',
                  "char_value____str": 'string    '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'case_sensitive',
                  "char_value____str": 'test      '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_sensitive',
                  "char_value____str": 'string    '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_sensitive',
                  "char_value____str": 'test      '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_sensitive',
                  "char_value____str": 'test      '}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_insensitive',
                  "char_value____str": 'test      '}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'case_insensitive',
                  "char_value____str": 'STRING    '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'case_insensitive',
                  "char_value____str": 'TEST      '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_insensitive',
                  "char_value____str": 'STRING    '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_insensitive',
                  "char_value____str": 'TEST      '}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_insensitive',
                  "char_value____str": 'TEST      '}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=STRING    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_case_sensitive',
                  "char_value____str": 'TEST      '}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=STRING    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def similar_to():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'similar_to',
                  "char_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'similar_to',
                  "char_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_similar_to',
                  "char_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'not_similar_to',
                  "char_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str%&char_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "char_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&char_value____str=str%&char_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    match_regex_with_case_sensitive()
    match_regex_with_case_insensitive()
    case_sensitive()
    case_insensitive()
    similar_to()

    # Varchar
    char_str_sample_data = create_example_data(5, varchar_value='string')
    char_test_sample_data = create_example_data(5, varchar_value='test')
    primary_key_list = [i[primary_key_name] for i in char_str_sample_data] + \
                       [i[primary_key_name] for i in char_test_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)

    # match_regex_with_case_sensitive/ dose not match_regex_with_case_sensitive
    def match_regex_with_case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "varchar_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_match_regex_with_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "varchar_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "varchar_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def match_regex_with_case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "varchar_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "varchar_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # does_not_match_regex_with_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "varchar_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "varchar_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "varchar_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "varchar_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'case_sensitive',
                  "varchar_value____str": 'string'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'case_sensitive',
                  "varchar_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_sensitive',
                  "varchar_value____str": 'string'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_sensitive',
                  "varchar_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_sensitive',
                  "varchar_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_insensitive',
                  "varchar_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'case_insensitive',
                  "varchar_value____str": 'STRING'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'case_insensitive',
                  "varchar_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_insensitive',
                  "varchar_value____str": 'STRING'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_insensitive',
                  "varchar_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_insensitive',
                  "varchar_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=STRING"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_case_sensitive',
                  "varchar_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=STRING"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def similar_to():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'similar_to',
                  "varchar_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'similar_to',
                  "varchar_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_similar_to',
                  "varchar_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'not_similar_to',
                  "varchar_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str%&varchar_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "varchar_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&varchar_value____str=str%&varchar_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    match_regex_with_case_sensitive()
    match_regex_with_case_insensitive()
    case_sensitive()
    case_insensitive()
    similar_to()

    # Text
    char_str_sample_data = create_example_data(5, text_value='string')
    char_test_sample_data = create_example_data(5, text_value='test')
    primary_key_list = [i[primary_key_name] for i in char_str_sample_data] + \
                       [i[primary_key_name] for i in char_test_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)

    # match_regex_with_case_sensitive/ dose not match_regex_with_case_sensitive
    def match_regex_with_case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "text_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_match_regex_with_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "text_value____str": 'str.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_sensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "text_value____str": 'tes.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def match_regex_with_case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "text_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'match_regex_with_case_insensitive',
                  "text_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # does_not_match_regex_with_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "text_value____str": 'STR.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "text_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_sensitive',
                  "text_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'does_not_match_regex_with_case_insensitive',
                  "text_value____str": 'TES.*'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=STR.*"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_sensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'case_sensitive',
                  "text_value____str": 'string'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'case_sensitive',
                  "text_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_sensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_sensitive',
                  "text_value____str": 'string'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_sensitive',
                  "text_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_sensitive',
                  "text_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_insensitive',
                  "text_value____str": 'test'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=string    "
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def case_insensitive():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'case_insensitive',
                  "text_value____str": 'STRING'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'case_insensitive',
                  "text_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_insensitive',
                  "text_value____str": 'STRING'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_insensitive',
                  "text_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_insensitive',
                  "text_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=STRING"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_case_sensitive',
                  "text_value____str": 'TEST'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=STRING"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    def similar_to():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'similar_to',
                  "text_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'similar_to',
                  "text_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        # not_case_insensitive
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_similar_to',
                  "text_value____str": 'string%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i not in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'not_similar_to',
                  "text_value____str": 'test%'}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i not in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str%&text_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "text_value____str_____matching_pattern": 'similar_to'}
        query_string = urlencode(OrderedDict(**params)) + "&text_value____str=str%&text_value____str=_es%"
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in char_str_sample_data:
            assert i in response.json()
        for i in char_test_sample_data:
            assert i in response.json()

    match_regex_with_case_sensitive()
    match_regex_with_case_insensitive()
    case_sensitive()
    case_insensitive()
    similar_to()


# test create a more than one data of float4/text/varchar type, and get many
def test_create_a_more_than_one_data_and_get_many_2():
    float_one = 5.5
    float_two = 10.7

    # float 4 <= will round down to the odd floating even
    # data  = 0.4
    # <= 0.4
    # result = []

    # data  = 0.4
    # <= 0.5
    # result = [0.4]

    num_one_sample_data = create_example_data(5, float4_value=float_one)
    num_two_sample_data = create_example_data(5, float4_value=float_two)
    primary_key_list = [i[primary_key_name] for i in num_one_sample_data] + \
                       [i[primary_key_name] for i in num_two_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)

    def greater_than_or_equal_to_Less_than_or_equal_to():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "float4_value____from_____comparison_operator": 'Greater_than_or_equal_to',
                  "float4_value____to_____comparison_operator": 'Less_than_or_equal_to',
                  "float4_value____from": float_one,
                  "float4_value____to": float_two}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in num_one_sample_data:
            assert i in response.json()
        for i in num_two_sample_data:
            assert i in response.json()

    # data = 10.7
    # < 10.7
    # still got 10.7 but if data is 10.6
    def less_than_or_equal_to_less_than():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "float4_value____from_____comparison_operator": 'Greater_than',
                  "float4_value____to_____comparison_operator": 'Less_than',
                  "float4_value____from": float_one,
                  "float4_value____to": float_two + 0.1}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in num_one_sample_data:
            assert i not in response.json()
        for i in num_two_sample_data:
            assert i in response.json()

    greater_than_or_equal_to_Less_than_or_equal_to()
    less_than_or_equal_to_less_than()

    # float 4 < will round down to the odd floating odd
    # data  = 0.3
    # <= 0.4
    # result = []

    # data  = 0.4
    # <= 0.5
    # result = [0.4]
    float_one = 5.5
    float_two = 10.6
    num_one_sample_data = create_example_data(5, float8_value=float_one)
    num_two_sample_data = create_example_data(5, float8_value=float_two)
    primary_key_list = [i[primary_key_name] for i in num_one_sample_data] + \
                       [i[primary_key_name] for i in num_two_sample_data]

    min_key = min(primary_key_list)
    max_key = max(primary_key_list)

    def greater_than_or_equal_to_Less_than_or_equal_to():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "float8_value____from_____comparison_operator": 'Greater_than_or_equal_to',
                  "float8_value____to_____comparison_operator": 'Less_than_or_equal_to',
                  "float8_value____from": float_one,
                  "float8_value____to": float_two}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 10
        for i in num_one_sample_data:
            assert i in response.json()
        for i in num_two_sample_data:
            assert i in response.json()

    def less_than_or_equal_to_less_than():
        params = {"primary_key____from": min_key,
                  "primary_key____to": max_key,
                  "float8_value____from_____comparison_operator": 'Greater_than',
                  "float8_value____to_____comparison_operator": 'Less_than',
                  "float8_value____from": float_one,
                  "float8_value____to": float_two + 0.1}
        query_string = urlencode(OrderedDict(**params))
        response = client.get(f'/test_get_many?{query_string}')
        response_data = response.json()
        assert len(response_data) == 5
        for i in num_one_sample_data:
            assert i not in response.json()
        for i in num_two_sample_data:
            assert i in response.json()

    greater_than_or_equal_to_Less_than_or_equal_to()
    less_than_or_equal_to_less_than()

# test order_by_columns regex validation


def test_get_many_with_ordering_unknown_column():
    try:
        response = client.get(f'/test_get_many?order_by_columns=testestset')
    except UnknownColumn as e:
        assert str(e) == "column testestset is not exited"
        return
    assert False


def test_get_many_with_ordering_with_default_order():
    response = client.get(f'/test_get_many?order_by_columns=primary_key&limit=10&offset=0')
    a = response.json()
    init = 0
    for i in a:
        assert i['primary_key'] >= init
        init = i['primary_key']


def test_get_many_with_ordering_with_ASC():
    response = client.get(f'/test_get_many?order_by_columns=primary_key:ASC&limit=10&offset=0')
    a = response.json()
    init = 0
    for i in a:
        assert i['primary_key'] >= init
        init = i['primary_key']


def test_get_many_with_ordering_with_DESC():
    response = client.get(f'/test_get_many?order_by_columns=primary_key:DESC&limit=10&offset=10')
    a = response.json()
    init = a[0]['primary_key']
    for i in a:
        assert i['primary_key'] == init
        init -= 1


def test_get_many_with_unknown_order_tyoe():
    try:
        response = client.get(f'/test_get_many?order_by_columns=primary_key:DESCSS&limit=10&offset=0')
    except UnknownOrderType as e:
        assert str(e) == 'Unknown order type DESCSS, only accept DESC or ASC'
        return
    assert False


def test_get_many_with_ordering_with_empty_input_list():
    try:
        response = client.get(f'/test_get_many?order_by_columns=')
    except Exception as e:
        assert False
    assert True



