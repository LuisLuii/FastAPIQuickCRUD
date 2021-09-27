import json

from starlette.testclient import TestClient


from src.fastapi_quickcrud.crud_router import crud_router_builder
from src.fastapi_quickcrud.misc.type import CrudMethods
from src.fastapi_quickcrud import sqlalchemy_to_pydantic
from tests.test_implementations.test_memory_sqlalchemy.api_test import app, UntitledTable256


UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.CREATE_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_create_one = crud_router_builder(db_model=UntitledTable256,
                                      crud_models=UntitledTable256Model,
                                      prefix="/test",
                                      tags=["test"],
    async_mode=True
                                      )

UntitledTable256Model = sqlalchemy_to_pydantic(UntitledTable256,
                                               crud_methods=[
                                                   CrudMethods.FIND_ONE
                                               ],
                                               exclude_columns=['bytea_value', 'xml_value', 'box_valaue'])

test_get_data = crud_router_builder(db_model=UntitledTable256,
                                    crud_models=UntitledTable256Model,
                                    prefix="/test",
                                    tags=["test"],
    async_mode=True
                                    )
[app.include_router(i) for i in [test_get_data, test_create_one]]

client = TestClient(app)
# create a sample data

headers = {
        'accept': '*/*',
        'Content-Type': 'application/json',
    }

data = '{ "bool_value": true, "char_value": "string", "date_value": "2021-07-26", "float4_value": 0, "float8_value": 0, "int2_value": 0, "int4_value": 0, "int8_value": 0, "interval_value": 0, "json_value": {}, "jsonb_value": {}, "numeric_value": 0, "text_value": "string", "time_value": "18:18:18", "timestamp_value": "2021-07-26T02:17:46.846Z", "timestamptz_value": "2021-07-26T02:17:46.846Z", "timetz_value": "18:18:18+00", "uuid_value": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "varchar_value": "string", "array_value": [ 0 ], "array_str__value": [ "string" ] }'

response = client.post('/test', headers=headers, data=data)
assert response.status_code == 201
response_data = response.json()
dict_data = json.loads(data)
sample_primary_key = response_data['primary_key']
'''
{
  "primary_key": 1013,
  "interval_value": 0, <- querying not supported
  "json_value": {},<- querying not supported
  "jsonb_value": {},<- querying not supported
  
  "array_value": [
    0
  ],
  "array_str__value": [
    "string"
  ]
}
'''
# try find the data by primary key
def test_get_by_primary_key_without_any_query_param():
    response = client.get(f'/test/{sample_primary_key}', headers=headers)
    assert response.status_code == 200
    assert response.json()['primary_key'] == sample_primary_key


#   "bool_value": true
# try find the data by primary key but false by bool
def test_get_by_primary_key_with_false_bool_query_param():

    response = client.get(f'/test/{sample_primary_key}?bool_value____list=false', headers=headers)
    assert response.status_code == 404
    response = client.get(f'/test/{sample_primary_key}?bool_value____list=true', headers=headers)
    assert response.status_code == 200
#   "char_value": "string    ",
# try find the data by primary key but false by char
def test_get_by_primary_key_with_false_char_query_param():
    response = client.get(f'/test/{sample_primary_key}?char_value____list=string1&char_value____list=string2',
                          headers=headers)
    assert response.status_code == 404
    response = client.get(f'/test/{sample_primary_key}?char_value____list=string&char_value____list=string1&',
                          headers=headers)
    assert response.status_code == 200

    # Like operator
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string1&char_value____str=%tri%&char_value____str_____matching_pattern=case_sensitive',
        headers=headers)
    assert response.status_code == 200
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string1&char_value____str=%tsri%&char_value____str_____matching_pattern=case_sensitive',
        headers=headers)
    assert response.status_code == 404

    # Ilike operator
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string1&char_value____str=%tRi%&char_value____str_____matching_pattern=case_insensitive',
        headers=headers)
    assert response.status_code == 200
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string1&char_value____str=%tsri%&char_value____str_____matching_pattern=case_insensitive',
        headers=headers)
    assert response.status_code == 404
    # not like operator
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string2&char_value____str=%strg%&char_value____str_____matching_pattern=not_case_sensitive',
        headers=headers)
    assert response.status_code == 200
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=string%&char_value____str=%strin%&char_value____str_____matching_pattern=not_case_sensitive',
        headers=headers)
    assert response.status_code == 404
    # not ilike operator
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=String2&char_value____str=%Strg%&char_value____str_____matching_pattern=not_case_insensitive',
        headers=headers)
    assert response.status_code == 200
    response = client.get(
        f'/test/{sample_primary_key}?char_value____str=STRING%&char_value____str=%TRI%&char_value____str_____matching_pattern=not_case_insensitive',
        headers=headers)
    assert response.status_code == 404
    # match regex with case sensitive operator
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stri.*&varchar_value____stg=str&char_value____str_____matching_pattern=match_regex_with_case_sensitive',
    #     headers=headers)
    # assert response.status_code == 200
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stg.*&char_value____str=stg&char_value____str_____matching_pattern=match_regex_with_case_sensitive',
    #     headers=headers)
    # assert response.status_code == 404
    # match regex with case insensitive operator
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=strI.*&char_value____str=STG&char_value____str_____matching_pattern=match_regex_with_case_insensitive',
    #     headers=headers)
    # assert response.status_code == 200
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stG.*&char_value____str=STG&char_value____str_____matching_pattern=match_regex_with_case_insensitive',
    #     headers=headers)
    # assert response.status_code == 404
    # does_not_match_regex_with_case_insensitive
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=strI.*&char_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive',
    #     headers=headers)
    # assert response.status_code == 404
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stG.*&char_value____str=STG&char_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive',
    #     headers=headers)
    # assert response.status_code == 200
    # dose not match regex with case sensitive operator
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stri.*&varchar_value____stg=str&char_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive',
    #     headers=headers)
    # assert response.status_code == 404
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=stg.*&char_value____str=stg&char_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive',
    #     headers=headers)
    # assert response.status_code == 200
    # similar_to
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=string&char_value____str=%(r|z)%&char_value____str_____matching_pattern=similar_to',
    #     headers=headers)
    # assert response.status_code == 200
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=str&char_value____str=(r|z)%&char_value____str_____matching_pattern=similar_to',
    #     headers=headers)
    # assert response.status_code == 404
    # not_similar_to
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=string%&char_value____str=%(r|z)%&char_value____str_____matching_pattern=not_similar_to',
    #     headers=headers)
    # assert response.status_code == 404
    # response = client.get(
    #     f'/test/{sample_primary_key}?char_value____str=str&char_value____str=(r|z)%&char_value____str_____matching_pattern=not_similar_to',
    #     headers=headers)
    # assert response.status_code == 200
#   "float4_value": 0,
# try find the data by primary key but false by float4
def test_get_by_primary_key_with_false_float4_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?float4_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?float4_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??float4_value____from=-2&float4_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?float4_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?float4_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?float4_value____from=0&float4_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float4_value____from=0&float4_value____to=0&float4_value____from_____comparison_operator=Greater_than_or_equal_to&float4_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float4_value____from=-1&float4_value____to=2&float4_value____from_____comparison_operator=Greater_than&float4_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float4_value____from=1&float4_value____to=2&float4_value____from_____comparison_operator=Greater_than&float4_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float4_value____from=1&float4_value____to=2&float4_value____from_____comparison_operator=Greater_than_or_equal_to&float4_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
#   "float8_value": 0,
# try find the data by primary key but false by float8
def test_get_by_primary_key_with_false_float8_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?float8_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?float8_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??float8_value____from=-2&float8_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?float8_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?float8_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?float8_value____from=0&float8_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float8_value____from=0&float8_value____to=0&float8_value____from_____comparison_operator=Greater_than_or_equal_to&float8_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float8_value____from=-1&float8_value____to=2&float8_value____from_____comparison_operator=Greater_than&float8_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float8_value____from=1&float8_value____to=2&float8_value____from_____comparison_operator=Greater_than&float8_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?float8_value____from=1&float8_value____to=2&float8_value____from_____comparison_operator=Greater_than_or_equal_to&float8_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
# try find the data by primary key but false by int2
# int2 0
def test_get_by_primary_key_with_false_int2_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?int2_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?int2_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??int2_value____from=-2&int2_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?int2_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?int2_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?int2_value____from=0&int2_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int2_value____from=0&int2_value____to=0&int2_value____from_____comparison_operator=Greater_than_or_equal_to&int2_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int2_value____from=-1&int2_value____to=2&int2_value____from_____comparison_operator=Greater_than&int2_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int2_value____from=1&int2_value____to=2&int2_value____from_____comparison_operator=Greater_than&int2_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int2_value____from=1&int2_value____to=2&int2_value____from_____comparison_operator=Greater_than_or_equal_to&int2_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
# try find the data by primary key but false by int4
# int 4 0
def test_get_by_primary_key_with_false_int4_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?int4_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?int4_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??int4_value____from=-2&int4_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?int4_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?int4_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?int4_value____from=0&int4_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int4_value____from=0&int4_value____to=0&int4_value____from_____comparison_operator=Greater_than_or_equal_to&int4_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int4_value____from=-1&int4_value____to=2&int4_value____from_____comparison_operator=Greater_than&int4_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int4_value____from=1&int4_value____to=2&int4_value____from_____comparison_operator=Greater_than&int4_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int4_value____from=1&int4_value____to=2&int4_value____from_____comparison_operator=Greater_than_or_equal_to&int4_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
# try find the data by primary key but false by int8
# int 8 0
def test_get_by_primary_key_with_false_int8_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?int8_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?int8_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??int8_value____from=-2&int8_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?int8_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?int8_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?int8_value____from=0&int8_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int8_value____from=0&int8_value____to=0&int8_value____from_____comparison_operator=Greater_than_or_equal_to&int8_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int8_value____from=-1&int8_value____to=2&int8_value____from_____comparison_operator=Greater_than&int8_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int8_value____from=1&int8_value____to=2&int8_value____from_____comparison_operator=Greater_than&int8_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?int8_value____from=1&int8_value____to=2&int8_value____from_____comparison_operator=Greater_than_or_equal_to&int8_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
# try find the data by primary key but false by numeric

# numeric 0
def test_get_by_primary_key_with_false_numeric_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?numeric_value____from=1', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?numeric_value____to=-1', headers=headers)
    assert response.status_code == 404

    # from - to
    response = client.get(f'/test/{sample_primary_key}??numeric_value____from=-2&numeric_value____to=-1',
                          headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?numeric_value____from=0', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?numeric_value____to=0', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?numeric_value____from=0&numeric_value____to=0',
                          headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?numeric_value____from=0&numeric_value____to=0&numeric_value____from_____comparison_operator=Greater_than_or_equal_to&numeric_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?numeric_value____from=-1&numeric_value____to=2&numeric_value____from_____comparison_operator=Greater_than&numeric_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?numeric_value____from=1&numeric_value____to=2&numeric_value____from_____comparison_operator=Greater_than&numeric_value____to_____comparison_operator=Less_than',
        headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(
        f'/test/{sample_primary_key}?numeric_value____from=1&numeric_value____to=2&numeric_value____from_____comparison_operator=Greater_than_or_equal_to&numeric_value____to_____comparison_operator=Less_than_or_equal_to',
        headers=headers)
    assert response.status_code == 404
# try find the data by primary key but false by text
#  "text_value": "string",
def test_get_by_primary_key_with_false_text_query_param():
    response = client.get(f'/test/{sample_primary_key}?text_value____list=string1&text_value____list=string2', headers=headers)
    assert response.status_code == 404
    response = client.get(f'/test/{sample_primary_key}?text_value____list=string&text_value____list=string1&', headers=headers)
    assert response.status_code == 200

    # Like operator
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string1&text_value____str=%tri%&text_value____str_____matching_pattern=case_sensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string1&text_value____str=%tsri%&text_value____str_____matching_pattern=case_sensitive', headers=headers)
    assert response.status_code == 404

    # Ilike operator
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string1&text_value____str=%tRi%&text_value____str_____matching_pattern=case_insensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string1&text_value____str=%tsri%&text_value____str_____matching_pattern=case_insensitive', headers=headers)
    assert response.status_code == 404
    # not like operator
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string2&text_value____str=%strg%&text_value____str_____matching_pattern=not_case_sensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?text_value____str=string&text_value____str=%strin%&text_value____str_____matching_pattern=not_case_sensitive', headers=headers)
    assert response.status_code == 404
    # not ilike operator
    response = client.get(f'/test/{sample_primary_key}?text_value____str=String2&text_value____str=%Strg%&text_value____str_____matching_pattern=not_case_insensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?text_value____str=STRING&text_value____str=%TRI%&text_value____str_____matching_pattern=not_case_insensitive', headers=headers)
    assert response.status_code == 404
    # match regex with case sensitive operator
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stri.*&varchar_value____stg=str&text_value____str_____matching_pattern=match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stg.*&text_value____str=stg&text_value____str_____matching_pattern=match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 404
    # match regex with case insensitive operator
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=strI.*&text_value____str=STG&text_value____str_____matching_pattern=match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stG.*&text_value____str=STG&text_value____str_____matching_pattern=match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 404
    # does_not_match_regex_with_case_insensitive
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=strI.*&text_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stG.*&text_value____str=STG&text_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 200
    # dose not match regex with case sensitive operator
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stri.*&varchar_value____stg=str&text_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=stg.*&text_value____str=stg&text_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 200
    # similar_to
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=string&text_value____str=%(r|z)%&text_value____str_____matching_pattern=similar_to', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=str&text_value____str=(r|z)%&text_value____str_____matching_pattern=similar_to', headers=headers)
    # assert response.status_code == 404
    # not_similar_to
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=string&text_value____str=%(r|z)%&text_value____str_____matching_pattern=not_similar_to', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?text_value____str=str&text_value____str=(r|z)%&text_value____str_____matching_pattern=not_similar_to', headers=headers)
    # assert response.status_code == 200
# try find the data by primary key but false by uuid
# def test_get_by_primary_key_with_false_uuid_query_param():
#     # In operator
#     response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa6&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9', headers=headers)
#     assert response.status_code == 200
#     response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afb6', headers=headers)
#     assert response.status_code == 404
#     # not In operator
#     response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa6&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list_____comparison_operator=Not_in', headers=headers)
#     assert response.status_code == 404
#     response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afb6&uuid_value____list_____comparison_operator=Not_in', headers=headers)
#     assert response.status_code == 200


    # # Equal operator
    # response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa6&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list_____comparison_operator=Equal', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afb6&uuid_value____list_____comparison_operator=Equal', headers=headers)
    # assert response.status_code == 404
    # # not Equal operator
    # response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa6&uuid_value____list_____comparison_operator=Not_equal', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afa9&uuid_value____list=3fa85f64-5717-4562-b3fc-2c963f66afb6&uuid_value____list_____comparison_operator=Not_equal', headers=headers)
    # assert response.status_code == 200
# try find the data by primary key but false by varchar
def test_get_by_primary_key_with_false_varchar_query_param():
    response = client.get(f'/test/{sample_primary_key}?varchar_value____list=string1&varchar_value____list=string2', headers=headers)
    assert response.status_code == 404
    response = client.get(f'/test/{sample_primary_key}?varchar_value____list=string&varchar_value____list=string1&', headers=headers)
    assert response.status_code == 200

    # Like operator
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string1&varchar_value____str=%tri%&varchar_value____str_____matching_pattern=case_sensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string1&varchar_value____str=%tsri%&varchar_value____str_____matching_pattern=case_sensitive', headers=headers)
    assert response.status_code == 404

    # Ilike operator
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string1&varchar_value____str=%tRi%&varchar_value____str_____matching_pattern=case_insensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string1&varchar_value____str=%tsri%&varchar_value____str_____matching_pattern=case_insensitive', headers=headers)
    assert response.status_code == 404
    # not like operator
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string2&varchar_value____str=%strg%&varchar_value____str_____matching_pattern=not_case_sensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string&varchar_value____str=%strin%&varchar_value____str_____matching_pattern=not_case_sensitive', headers=headers)
    assert response.status_code == 404
    # not ilike operator
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=String2&varchar_value____str=%Strg%&varchar_value____str_____matching_pattern=not_case_insensitive', headers=headers)
    assert response.status_code == 200
    response = client.get(f'/test/{sample_primary_key}?varchar_value____str=STRING&varchar_value____str=%TRI%&varchar_value____str_____matching_pattern=not_case_insensitive', headers=headers)
    assert response.status_code == 404
    # match regex with case sensitive operator
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stri.*&varchar_value____stg=str&varchar_value____str_____matching_pattern=match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stg.*&varchar_value____str=stg&varchar_value____str_____matching_pattern=match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 404
    # match regex with case insensitive operator
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=strI.*&varchar_value____str=STG&varchar_value____str_____matching_pattern=match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stG.*&varchar_value____str=STG&varchar_value____str_____matching_pattern=match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 404
    # does_not_match_regex_with_case_insensitive
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=strI.*&varchar_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stG.*&varchar_value____str=STG&varchar_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive', headers=headers)
    # assert response.status_code == 200
    # dose not match regex with case sensitive operator
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stri.*&varchar_value____stg=str&varchar_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=stg.*&varchar_value____str=stg&varchar_value____str_____matching_pattern=does_not_match_regex_with_case_sensitive', headers=headers)
    # assert response.status_code == 200
    # similar_to
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string&varchar_value____str=%(r|z)%&varchar_value____str_____matching_pattern=similar_to', headers=headers)
    # assert response.status_code == 200
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=str&varchar_value____str=(r|z)%&varchar_value____str_____matching_pattern=similar_to', headers=headers)
    # assert response.status_code == 404
    # not_similar_to
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=string&varchar_value____str=%(r|z)%&varchar_value____str_____matching_pattern=not_similar_to', headers=headers)
    # assert response.status_code == 404
    # response = client.get(f'/test/{sample_primary_key}?varchar_value____str=str&varchar_value____str=(r|z)%&varchar_value____str_____matching_pattern=not_similar_to', headers=headers)
    # assert response.status_code == 200
# query by range of date field
def test_get_by_primary_key_with_false_date_range_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-27', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?date_value____to=2021-07-24', headers=headers)
    assert response.status_code == 404

    # from - to

    response = client.get(f'/test/{sample_primary_key}??date_value____from=2021-07-21&date_value____to=2021-07-24', headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-24', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?date_value____to=2021-07-27', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-24&date_value____to=2021-07-27', headers=headers)
    assert response.status_code == 200

    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-26&date_value____to=2021-07-26&date_value____from_____comparison_operator=Greater_than_or_equal_to&date_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-25&date_value____to=2021-07-27&date_value____from_____comparison_operator=Greater_than&date_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-26&date_value____to=2021-07-26&date_value____from_____comparison_operator=Greater_than&date_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?date_value____from=2021-07-27&date_value____to=2021-07-29&date_value____from_____comparison_operator=Greater_than_or_equal_to&date_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 404
def test_get_by_primary_key_with_false_time_range_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?time_value____from=19:18:18', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?time_value____to=17:18:18', headers=headers)
    assert response.status_code == 404

    # from - to

    response = client.get(f'/test/{sample_primary_key}?time_value____from=10:18:18&time_value____to=17:18:18', headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?time_value____from=10:18:18', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?time_value____to=19:18:18', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?time_value____from=10:18:18&time_value____to=19:18:18', headers=headers)
    assert response.status_code == 200


    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?time_value____from=18:18:18&time_value____to=18:18:18&time_value____from_____comparison_operator=Greater_than_or_equal_to&time_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?time_value____from=18:18:17&time_value____to=18:18:19&time_value____from_____comparison_operator=Greater_than&time_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?time_value____from=18:18:18&time_value____to=18:18:18&time_value____from_____comparison_operator=Greater_than&time_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?time_value____from=19:18:18&time_value____to=19:19:18&time_value____from_____comparison_operator=Greater_than_or_equal_to&time_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 404
def test_get_by_primary_key_with_false_timestamp_range_query_param():
    #   "timestamp_value": "2021-07-26T02:17:46.846000",

    # from
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-27T02:17:46.846000', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____to=2021-07-25T02:17:46.846000', headers=headers)
    assert response.status_code == 404

    # from - to

    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-20T02:17:46.846000&timestamp_value____to=2021-07-25T02:17:46.846000', headers=headers)
    assert response.status_code == 404

    # success from
    a = sample_primary_key

    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-24T02:17:46.846000', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____to=2021-07-28T02:17:46.846000', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-24T02:17:46.846000&timestamp_value____to=2021-07-28T02:17:46.846000', headers=headers)
    assert response.status_code == 200



    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-26T02:17:46.846&timestamp_value____to=2021-07-26T02:17:46.846Z&timestampt_value____from_____comparison_operator=Greater_than_or_equal_to&timestampt_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-26T02:17:46.746Z&timestamp_value____to=2021-07-26T02:17:46.946Z&timestampt_value____from_____comparison_operator=Greater_than&timestampt_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-26T02:17:46.846Z&timestamp_value____to=2021-07-26T02:17:46.946Z&timestamp_value____from_____comparison_operator=Greater_than&timestamp_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamp_value____from=2021-07-26T02:17:46.856Z&timestamp_value____to=2021-07-26T02:17:46.986Z&timestamp_value____from_____comparison_operator=Greater_than_or_equal_to&timestamp_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 404
def test_get_by_primary_key_with_false_timetz_range_query_param():
    # from
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from=19%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?timetz_value____to=17%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 404

    # from - to

    response = client.get(f'/test/{sample_primary_key}?timetz_value____from=16%3A18%3A18%2B00%3A00&timetz_value____to=17%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 404
    # success from

    response = client.get(f'/test/{sample_primary_key}?timetz_value____from=17%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?timetz_value____to=19%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from=16%3A18%3A18%2B00%3A00&timetz_value____to=19%3A18%3A18%2B00%3A00', headers=headers)
    assert response.status_code == 200


    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from_____comparison_operator=Greater_than&timetz_value____to_____comparison_operator=Less_than&timetz_value____from=17%3A18%3A18%2B00&timetz_value____to=19%3A18%3A18%2B00', headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from_____comparison_operator=Greater_than_or_equal_to&timetz_value____to_____comparison_operator=Less_than_or_equal_to&timetz_value____from=18%3A18%3A18%2B00&timetz_value____to=18%3A19%3A18%2B00', headers=headers)
    assert response.status_code == 200


    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from_____comparison_operator=Greater_than&timetz_value____to_____comparison_operator=Less_than&timetz_value____from=16%3A18%3A18%2B00&timetz_value____to=18%3A18%3A18%2B00', headers=headers)
    assert response.status_code == 404
    # failure from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timetz_value____from_____comparison_operator=Greater_than_or_equal_to&timetz_value____to_____comparison_operator=Less_than_or_equal_to&timetz_value____from=16%3A18%3A18%2B00&timetz_value____to=17%3A19%3A18%2B00', headers=headers)
    assert response.status_code == 404
def test_get_by_primary_key_with_false_timestamptz_range_query_param():
    #   "timestamp_value": "2021-07-26T02:17:46.846000",

    # from
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-27T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 404

    # to
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____to=2021-07-25T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 404

    # from - to

    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-27T02%3A17%3A46.846000%2B00%3A00&timestamptz_value____to=2021-07-28T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 404

    # success from

    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-20T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 200
    # success to
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____to=2021-07-29T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 200

    # success from - to
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-20T02%3A17%3A46.846000%2B00%3A00&timestamptz_value____to=2021-07-27T02%3A17%3A46.846000%2B00%3A00', headers=headers)
    assert response.status_code == 200


    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-26T02%3A17%3A46.846Z&timestamptz_value____to=2021-07-26T02%3A17%3A46.846Z&timestamptz_value____from_____comparison_operator=Greater_than_or_equal_to&timestamptz_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 200
    # success from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-26T02%3A17%3A46.800Z&timestamptz_value____to=2021-07-26T02%3A17%3A46.946Z&timestamptz_value____from_____comparison_operator=Greater_than&timestamptz_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 200

    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-26T02%3A17%3A46.846Z&timestamptz_value____to=2021-07-26T02%3A17%3A46.900Z&timestamptz_value____from_____comparison_operator=Greater_than&timestamptz_value____to_____comparison_operator=Less_than', headers=headers)
    assert response.status_code == 404
    # failed from - to with special operator
    response = client.get(f'/test/{sample_primary_key}?timestamptz_value____from=2021-07-26T02%3A17%3A46.847Z&timestamptz_value____to=2021-07-26T02%3A17%3A46.946Z&timestamptz_value____from_____comparison_operator=Greater_than_or_equal_to&timestamptz_value____to_____comparison_operator=Less_than_or_equal_to', headers=headers)
    assert response.status_code == 404


