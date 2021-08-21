#  FastAPI Quick CRUD




[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c2a6306f7f0a41948369d80368eb7abb)](https://www.codacy.com/gh/LuisLuii/FastAPIQuickCRUD/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LuisLuii/FastAPIQuickCRUD&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/LuisLuii/FastAPIQuickCRUD/badge.svg?branch=feature/code_coverage)](https://coveralls.io/github/LuisLuii/FastAPIQuickCRUD?branch=develop)
[![CircleCI](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/develop.svg?style=svg)](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/develop)
[![PyPidownload](https://img.shields.io/pypi/dm/fastapi-quickcrud)](https://pypi.org/project/fastapi-quickcrud)
[![SupportedVersion](https://img.shields.io/pypi/pyversions/fastapi-quickcrud)](https://pypi.org/project/fastapi-quickcrud)
[![SupportedVersion](https://img.shields.io/pypi/status/fastapi-quickcrud)](https://pypi.org/project/fastapi-quickcrud)

---

# What is this?

I believe that everyone who's working with FastApi and building some RESTful of CRUD services,
The `FastAPI Quick CRUD` can generate CRUD in FastApi with SQLAlchemy schema

![docs page](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/page_preview.png?raw=true)

## Feature

- Convert Sqlalchemy Declarative Base class of PostgreSQL Database to CRUD API 
    - Get one
    - Get many
    - Update one
    - Update many
    - Patch one
    - Patch many
    - Create/Upsert one
    - Create/Upsert many
    - Delete One
    - Delete Many
    - Post Redirect Get


## Installation
```commandline
pip install fastapi-quickcrud
```
## Quick Use

1. Build a sample table with Sqlalchemy

    Strongly recommend you use [sqlacodegen](https://pypi.org/project/sqlacodegen/) to  generate the sql schema

    ```python
    from sqlalchemy import create_engine
    from sqlalchemy import *
    from sqlalchemy.dialects.postgresql import *
    from sqlalchemy.orm import *
   
    Base = declarative_base()
    metadata = Base.metadata
    engine = create_engine('postgresql://<user name>:<password>@<host>:<port>/<database name>', 
                            future=True, 
                            echo=True,
                            pool_use_lifo=True,
                            pool_pre_ping=True, 
                            pool_recycle=7200)

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
    from fastapi_quickcrud import crud_router_builder
    from fastapi_quickcrud import CrudService
    from fastapi_quickcrud import CrudMethods
    from fastapi_quickcrud import sqlalchemy_to_pydantic
    ```

4. convert the sqlalchemy model to Pydantic model

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

    - argument:
        - db_model: ```SQLALchemy Declarative Base Class```
        - async_mode: ```bool```
          - set True if using async SQLALchemy
        - crud_methods: ```CrudMethods```
            - examples
              - CrudMethods.FIND_ONE
              - CrudMethods.FIND_MANY
              - CrudMethods.UPDATE_ONE
              - CrudMethods.UPDATE_MANY
              - CrudMethods.PATCH_ONE
              - CrudMethods.PATCH_MANY
              - CrudMethods.UPSERT_ONE
              - CrudMethods.UPSERT_MANY
              - CrudMethods.DELETE_ONE
              - CrudMethods.DELETE_MANY
              - CrudMethods.POST_REDIRECT_GET

        - exclude_columns: set the columns that not to be operated but the columns should nullable or set the default value)

5. user CrudRouter to register API
                                            
    - db_session: `session generator` 
        - example:
            - sync SQLALchemy:
                ```python
                    def get_transaction_session():
                        try:
                            db = sessionmaker(...)
                            yield db
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            raise e
                        finally:
                            db.close()
              ```
            - Async SQLALchemy
                ```python
                async def get_transaction_session() -> AsyncSession:
                    async with async_session() as session:
                        async with session.begin():
                            yield session
                ```

    - db_model: `SQLALchemy Declarative Base Class`

    - async_mode: `bool` if your db session is async
    
    - autocommit: `bool` if you don't need to commit by your self    

    - crud_models: `sqlalchemy_to_pydantic` 

    - prefix, tags: extra argument for include_router() of APIRouter() of fastapi

    ```python
    	new_route_3 = crud_router_builder(db_session=get_transaction_session,
                                          crud_service=UntitledTable256_service,
                                          crud_models=test_crud_model,
                                          prefix="/crud_test",
                                          dependencies = [],
                                          tags=["Example"]
                                          )
    ```


## Design

- Query Operation will look like that when python type of column is 
  - string
    - support Approximate String Matching that require this 
        - (<column_name>____str, <column_name>____str_____matching_pattern)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![string](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/string_query.png?raw=true)
  - numeric 
    - support Range Searching from and to
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![numeric](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/numeric_query.png?raw=true)
  - datetime 
    - support Range Searching from and to
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - support In-place Operation, get the value of column in the list of input
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![datetime](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/time_query.png?raw=true)
  - Pagination 
    - limit
    - offset
    - order by
    
![Pagination](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/Pagination_query.png?raw=true)  
      
- Approximate String Matching  
    ref: https://www.postgresql.org/docs/9.3/functions-matching.html
    - example:
      
        query
      
        ```text
      /test_CRUD?
      char_value____str_____matching_pattern=match_regex_with_case_sensitive&
      char_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive&
      char_value____str_____matching_pattern=case_sensitive&
      char_value____str_____matching_pattern=not_case_insensitive&
      char_value____str=a&
      char_value____str=b
      ```
      
    - generated sql 
        ```sql
        SELECT *
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
    
![in](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/in_query.png?raw=true)  
    - generated sql if user select Equal operation and input True and False
```sql        
        select * FROM untitled_table_256 
        WHERE untitled_table_256.bool_value = true OR 
        untitled_table_256.bool_value = false
```     
        
- Range Searching
    - Range Searching support the following operation
    
![greater](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/greater_query.png?raw=true)  
    
![less](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/less_query.png?raw=true)  
  - generated sql 
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
- Please don't use composite unique constraint and the single unique constraint at the same time
    - except the single one unique constraint is primary key which be contained into composite unique constraint
        ```python
        class Example(Base):
            __tablename__ = 'example'
            __table_args__ = (
                UniqueConstraint('p_id', 'test'),
            )
        
            p_id = Column(Integer, primary_key=True, unique=True)
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


## Alias

Alias is supported already

usage:

```python
id = Column('primary_key',Integer, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
```

you can use info argument to set the alias name of column, 
and use synonym to map the column between alias column and original column

```python
id = Column(Integer, info={'alias_name': 'primary_key'}, primary_key=True, server_default=text("nextval('untitled_table_256_id_seq'::regclass)"))
primary_key = synonym('id')
```

#### FastAPI_quickcrud Response Status Code standard 


When you ask for a specific resource, say a user or with query param, and the user doesn't exist

 ```GET: get one : https://0.0.0.0:8080/api/:userid?xx=xx```
 ```UPDATE: update one : https://0.0.0.0:8080/api/:userid?xx=xx```
 ```PATCH: patch one : https://0.0.0.0:8080/api/:userid?xx=xx```
 ```DELETE: delete one : https://0.0.0.0:8080/api/:userid?xx=xx```
 
then fastapi-qucikcrud should return 404. In this case, the client requested a resource that doesn't exist.

----

In the other case, you have an api that operate data on batch in the system using the following url:

 ```GET: get many : https://0.0.0.0:8080/api/user?xx=xx```
 ```UPDATE: update many : https://0.0.0.0:8080/api/user?xx=xx```
 ```DELETE: delete many : https://0.0.0.0:8080/api/user?xx=xx```
 ```PATCH: patch many : https://0.0.0.0:8080/api/user?xx=xx```

If there are no users in the system, then, in this case, you should return 204.


### TODO

- support [databases](https://pypi.org/project/databases/) as db connector -> the next task
- support pony 
- support MYSQL and Sqllite
- Manually create the model for each CRUD API 
- Apply the comment of each column into docs
