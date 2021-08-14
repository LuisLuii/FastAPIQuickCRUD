#  FastAPI Quick CRUD

This is a CRUD router builder, which allow you to build Pydantic model automatically via SQLAlchemy schema, and provided that a simple but comprehensive CRUD API:

- Get one
- Get many
- Update one
- Update many
- Patch one
- Patch many
- Create one
- Create many
- Upsert One
- Upsert Many
- Delete One
- Delete Many
![docs page](pic/page_preview.png)


- Query Operation will look like that when python type of column is 
  - string
    - support Approximate String Matching that require this 
        - (<column_name>____str, <column_name>____str_____matching_pattern)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    - ![string](pic/string_query.png)
  - numeric 
    - support Range Searching from and to
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    ![numeric](pic/numeric_query.png)
  - datetime 
    - support Range Searching from and to
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    ![datetime](pic/time_query.png)
  - Pagination 
    - limit
    - offset
    - order by
    ![Pagination](pic/Pagination_query.png)  
      
- Approximate String Matching  
    ref: https://www.postgresql.org/docs/9.3/functions-matching.html
    - example:
        if query is ```GET /test_CRUD?char_value____str_____matching_pattern=match_regex_with_case_sensitive&char_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive&char_value____str_____matching_pattern=case_sensitive&char_value____str_____matching_pattern=not_case_insensitive&char_value____str=a&char_value____str=b```
    - the sql will look like that
        ```sql
        SELECT untitled_table_256.*
        FROM untitled_table_256 
        WHERE (untitled_table_256.char_value ~ 'a') OR 
        (untitled_table_256.char_value ~ 'b' OR 
        (untitled_table_256.char_value !~* 'a') OR 
        (untitled_table_256.char_value !~* 'b' OR 
        untitled_table_256.char_value LIKE 'a' OR 
        untitled_table_256.char_value LIKE 'b' OR 
        untitled_table_256.char_value NOT ILIKE 'a' 
        OR untitled_table_256.char_value NOT ILIKE 'b'
        ```
      
- In-place Operation
    - In-place support the following operation
    ![in](pic/in_query.png)  
    - query example
      * if user select Equal operation and input True and False
        ```sql
        select * FROM untitled_table_256 
        WHERE untitled_table_256.bool_value = true OR 
        untitled_table_256.bool_value = false
        ```  
        
- Range Searching
    - Range Searching support the following operation
    ![greater](pic/greater_query.png)  
    ![less](pic/less_query.png)  
  - sql is look like that
    ```sql
    select * from untitled_table_256
    WHERE untitled_table_256.date_value > %(date_value_1)s 
    ```
    ```sql
    select * from untitled_table_256
    WHERE untitled_table_256.date_value < %(date_value_1)s 
    ```

Also support your custom dependency for each api

# constraint

- Please use composite unique constraint if there are more than one unique fields
- Please don't use composite unique constraint and the single unique constraint in the same time
    - except the single one unique constraint is primary key which be contained into composite unique constraint

        Don't declare the `unique=True` if the column is primary key

        ```python
        class Example(Base):
            __tablename__ = 'example'
            __table_args__ = (
                UniqueConstraint('p_id', 'test'),
            )

            p_id = Column(Integer, primary_key=True)
            test = Column(Integer)
            test_1 = Column(Text)
        ```

- Primary key is required but not support composite primary key
- The field of api will be optional if there is default value or is nullable or server_default is set
- The value of server_default did not support show on OpenAPI
- The field of api will be required if there is no default value of the column or is not nullable
- Some type of columns are not support in query:
    - INTERVAL
    - JSON
    - JSONB
    - H-STORE
    - ARRAY
    - BYTE
    - Geography
    - box
    - line
    - point
    - lseg
    - polygon
    - inet
    - macaddr

- Automap() of Sqlalchemy is not support


## Quick Use
```angular2html
pip install quick-crud
```
1. Build a sample table with Sqlalchemy

    Strongly recommend you use `[sqlacodegen](https://pypi.org/project/sqlacodegen/)` to  generate the sql schema

    ```python
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine('postgresql://<user name>:<password>@<host>:<port>/<database name>', future=True, echo=True,
                           pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)

    class CRUDTest(Base):
        __tablename__ = 'crud_test'
        __table_args__ = (
            UniqueConstraint('id','float4_value', 'int4_value'),
        )

        id = Column(Integer, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
        bool_value = Column(Boolean, nullable=False, server_default=text("false"))
        bytea_value = Column(LargeBinary)
        char_value = Column(CHAR(10))
        date_value = Column(Date, server_default=text("now()"))
        float4_value = Column(Float, nullable=False)
        float8_value = Column(Float(53), nullable=False, server_default=text("10.10"))
        int2_value = Column(SmallInteger, nullable=False)
        int4_value = Column(Integer, nullable=False)
        int8_value = Column(BigInteger, default=99)
        interval_value = Column(INTERVAL)
        json_value = Column(JSON)
        jsonb_value = Column(JSONB(astext_type=Text()))
        numeric_value = Column(Numeric)
        text_value = Column(Text)
        time_value = Column(Time)
        timestamp_value = Column(DateTime)
        timestamptz_value = Column(DateTime(True))
        timetz_value = Column(Time(True))
        uuid_value = Column(UUID(as_uuid=True))
        varchar_value = Column(String)
        array_value = Column(ARRAY(Integer()))
        array_str__value = Column(ARRAY(String()))

    CRUDTest.__table__.create(engine)
    ```

2. prepare a database connection 

    ```python
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    def get_transaction_session():
        try:
            db = session()
            yield db
        finally:
            db.close()
    ```

3. import the required module

    ```python
    from fastapi_quickcrud import crud_router
    from fastapi_quickcrud import CrudService
    from fastapi_quickcrud import CrudMethods
    from fastapi_quickcrud import sqlalchemy_to_pydantic
    ```

4. register CrudService  

    ```python
    test_crud_service = CrudService(model=CRUDTest)
    ```

5. covent the sqlalchemy model to Pydantic model

    ```python
    test_crud_model = sqlalchemy_to_pydantic(db_model = CRUDTest,
                                             crud_methods=[
                                                       CrudMethods.FIND_MANY,
                                                       CrudMethods.FIND_ONE,
                                                       CrudMethods.UPSERT_ONE,
                                                       CrudMethods.UPDATE_MANY,
                                                       CrudMethods.UPDATE_ONE,
                                                       CrudMethods.DELETE_ONE,
                                                       CrudMethods.DELETE_MANY,
                                                       CrudMethods.PATCH_MANY,
                                                       CrudMethods.PATCH_ONE,

                                               ],
                                             exclude_columns=[])

    ```

    argument: 

    db_model: Sqlalchemy Schema

    crud_methods: CRUD api

    - example

        crud_methods: build the curd method

        FASTCRUD supports these crud method(`CrudMethods`)

        - FIND_ONE
        - FIND_MANY
        - UPDATE_ONE
        - UPDATE_MANY
        - PATCH_ONE
        - PATCH_MANY
        - CREATE_ONE
        - CREATE_MANY
        - UPSERT_ONE
        - UPSERT_MANY
        - DELETE_ONE
        - DELETE_MANY

    exclude_columns: Same columns will not be operation (if the column is nullable or has default value)

6. user CrudRouter to register API

    db_session: `get_transaction_session`

    crud_service: `CrudService`

    crud_models: `sqlalchemy_to_pydantic` 

    prefix, tags: extra argument for include_router() of APIRouter() of fastapi

    ```python
    	new_route_3 = CrudRouter(db_session=get_transaction_session,
                             crud_service=UntitledTable256_service,
                             crud_models=test_crud_model,
                             prefix="/crud_test",
                             tags=["Example"]
                             )
    ```

- `GET`

    Http status code of api response is follow the rule when data not found in `FIND_ONE` and `FIND_MANY`:

    Collection resources(`FIND_MANY`):

    - /user
    - /user/me/friends

    200 with an empty list

    Object resource(`FIND_ONE`):

    - /user/$id

    204 

    - FIND_ONE

        ### This api will find the data with strict searching

        Url:

        /end point name 

        - The api did not support the following data types:
            - INTERVAL
            - JSON
            - JSONB
            - H-STORE
            - ARRAY
            - BYTE
        - The api supports the following data types:
            - Boolean
            - Character types such as `char`, `varchar`, and `text`.
            - Numeric types such as integer and floating-point number.
            - Temporal types such as date, time, timestamp but interval

                Temporal types related columns query is strict, but it is support date range filter, e.g.  you want to get data without deleted_at < now()

            - UUID for storing Universally Unique Identifiers

        - Feature
            - search by date range for date related columns
            - search the data by primary key and allow to filter with additional columns(such as now()>deleted_at)
        - Other thing
            - If data is found, the `x-total-count` in the header should be 1

        response status code:

        200 - get data success

        200(with empty list in response body) - request success but data not found by the query parameters

    - FIND_MANY

        ### This api supports Approximate String Matching(Fuzzy Matching)

        Url:

        /end point name 

        - The api did not support the following data types:
            - INTERVAL
            - JSON
            - JSONB
            - H-STORE
            - ARRAY
            - BYTE
        - The api supports the following data types:
            - Boolean
            - Character types such as `char`, `varchar`, and `text`.

                The query operation of Character type columns is according with the `string_matching_patterns`

            - Numeric types such as integer and floating-point number.
            - Temporal types such as date, time, timestamp but interval

                Temporal types related columns query is strict, but it is support date range filter, e.g.  you want to get data without deleted_at < now()

            - UUID for storing Universally Unique Identifiers

        - Feature
            - Pagination
                - limit
                - offset
                - order by
            - Sql approximate string matching
                - MatchRegexWithCaseSensitive
                - MatchRegexWithCaseInsensitive
                - DoesNotMatchRegexWithCaseInsensitive
                - DoesNotMatchRegexWithCaseSensitive
                - Ilike
                - Like
                - SimilarTo
            - search by date range for date related columns
        - Other thing
            - `x-total-count` in header will show how many date match your query

        response status code:

        200 - get data success

        204 - request success but data not found by the query parameters

- UPDATE

    The required or optional fields in request body is depended on the nullable and column default in the table schema. 

    The field will be optional if the columns is nullable and there is default value 

    `default input do not support server_default in Sqlalchemy schema`

    example:

    if the field is using `server_default` with Sqlalchemy schema

    - Optional field
    - It can default input
    - The Openapi will not show the default value

    if the field is using `default` with Sqlalchemy schema

    - Optional field
    - It can default input
    - The Openapi will show the default value
- PATCH & DELETE

    The following api supports url parameter (primary key) as a command to the resource to limit the scope of the current request. And a query parameters as a command to strict filter the scope of data.

    the filtering data number should only be one(filter by primary key), and data will be updated by request body if there is data after filter by query parameters.

    Http status code of api response is follow the rule:

    200 - operation success

    204 - No data if filter by query parameters

    - PATCH_ONE

        url:

        /`{primary key name}`?`column_name=xxx`

        Query:

        You Should Know:

        - the primary key path parameter is required
        - the query parameter allows to all the columns
        - query and response binary data is not support, use `exclude` argument in `sqlalchemy_to_pydantic`

        the api supports the following data types:

        - Boolean
        - Character types such as `char`, `varchar`, and `text`.
        - Numeric types such as integer and floating-point number.
        - Temporal types such as date, time, timestamp, and interval

            Temporal types related columns query is strict, but it is support date range filter, e.g.  you want to get data without deleted_at < now()

        - UUID for storing Universally Unique Identifiers

        Request Body

        Which columns you want to be updated

        Return

        All the columns without the columns in exclude list

    - DELETE_ONE

        Http status code of api response is follow the rule:

        200 - delete success

        204 - deletion target of query filter not found

        url:

        /`{primary key name}`?`column_name=xxx`

        Query:

        You Should Know:

        - the primary key path parameter is required
        - the query parameter allows to all the columns
        - query and response binary data is not support, use `exclude` argument in `sqlalchemy_to_pydantic`

        the api supports the following data types:

        - Boolean
        - Character types such as `char`, `varchar`, and `text`.
        - Numeric types such as integer and floating-point number.
        - Temporal types such as date, time, timestamp, and interval

            Temporal types related columns query is strict, but it is support date range filter, e.g.  you want to get data without deleted_at < now()

        - UUID for storing Universally Unique Identifiers

        Request Body

        Which columns you want to be updated

        Return

        return the primary key value

- POST_REDIRECT_GET

    This API supports that create one data and redirect to get one api if create success, and response 409 if conflict

    - POST_REDIRECT_GET

        url:

        /`end point`?`conflict_handling=`

        Query:

        You Should Know:

        - abort

            response `409`

        - redirect_get

            redirect to the url of `FIND_ONE` API with primary key of you input

- UPSERT

    This API supports that insert one or more than one data, and update the existing data if conflicting

    - UPSERT_MANY

        url:

        /`end point`

    - UPSERT_ONE

        url:

        /

    there are on_conflict_columns and update_columns in request body;

    the `on_conflict_columns` should be  composite unique construct columns in that table, and the other columns should be set as `update_columns`

# Alias

Alias is supported already

usage:

```python
id = Column('primary_key',Integer, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
```

you can use info argument wait alias_name key 

modify the id to alias name

```python
id = Column(Integer, info={'alias_name': 'primary_key'}, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
primary_key = synonym('id')
```
