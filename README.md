#  FastAPI Quick CRUD

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c2a6306f7f0a41948369d80368eb7abb?style=flat-square)](https://www.codacy.com/gh/LuisLuii/FastAPIQuickCRUD/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LuisLuii/FastAPIQuickCRUD&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/LuisLuii/FastAPIQuickCRUD/badge.svg?branch=main)](https://coveralls.io/github/LuisLuii/FastAPIQuickCRUD?branch=main)
[![CircleCI](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/main.svg?style=svg)](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/main)
[![PyPidownload](https://img.shields.io/pypi/dm/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)
[![SupportedVersion](https://img.shields.io/pypi/pyversions/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)
[![develop dtatus](https://img.shields.io/pypi/status/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)

---


![docs page](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/page_preview.png?raw=true)


- [Introduction](#introduction)
  - [Advantage](#advantage)
  - [Constraint](#constraint)
- [Getting started](#getting-started)
  - [Installation](#installation)
  - [Usage](#usage)
- [Design](#design)
  - [Path Parameter](#path-parameter)
  - [Query Parameter](#query-parameter)
  - [Request Body](#request-body)
  - [Upsert](#upsert)


# Introduction

I believe that everyone who's working with FastApi and building some RESTful of CRUD services, wastes the time to writing similar code for simple CRUD every time

`FastAPI Quick CRUD` can generate CRUD in FastApi with SQLAlchemy schema. 

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

`FastAPI Quick CRUD`is developed based on SQLAlchemy `1.4.23` version and supports sync and async.

## Advantage

  - [x] **Support SQLAlchemy 1.4** - Allow you build a fully asynchronous python service, also supports synchronization.
  
  - [x] **Support Pagination** - Get many API support `order by` `offset` `limit` field in API

  - [x] **Rich FastAPI CRUD router generation** - Many operations of CRUD are implemented to complete the development and coverage of all aspects of basic CRUD.

  - [x] **CRUD route automatically generated** - Support Declarative class definitions and Imperative table
    
  - [x] **Flexible API request** - `UPDATE ONE/MANY` `FIND ONE/MANY` `PATCH ONE/MANY` `DELETE ONE/MANY` supports Path Parameters (primary key) and Query Parameters as a command to the resource to filter and limit the scope of the scope of data in request.
    
## Constraint
   
  - ❌ If there are multiple unique constraints, please use composite unique constraints instead
  - ❌ Composite primary key is not support
  - ❌ Not Support API requests with specific resource `xxx/{primary key}` when table have not primary key; 
    - `UPDATE ONE`
    - `FIND ONE`
    - `PATCH ONE` 
    - `DELETE ONE` 
  - ❌ [Alias](#alias) is not support for imperative table yet
  - ❌ Some types of columns are not supported as query parameter
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

# Getting started

## Installation

```bash
pip install fastapi-quickcrud
```

## Usage

Start PostgreSQL using:
```bash
docker run -d -p 5432:5432 --name mypostgres --restart always -v postgresql-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=1234 postgres
```

#### Simple Code (get more example from `./example`)


1. Build a sample table with Sqlalchemy

    Strongly recommend you use [sqlacodegen](https://pypi.org/project/sqlacodegen/) to  generate the sql schema

    ```python
    from sqlalchemy import create_engine
    from sqlalchemy import *
    from sqlalchemy.dialects.postgresql import *
    from sqlalchemy.orm import *
   
    Base = declarative_base()
    metadata = Base.metadata
    engine = create_engine('postgresql://postgres:1234@127.0.0.1:5432/postgres', 
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
    from fastapi_quickcrud import CrudMethods
    from fastapi_quickcrud import sqlalchemy_to_pydantic
    from fastapi_quickcrud import sqlalchemy_table_to_pydantic
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
        - crud_methods: ```CrudMethods```
            > - CrudMethods.FIND_ONE
            > - CrudMethods.FIND_MANY
            > - CrudMethods.UPDATE_ONE
            > - CrudMethods.UPDATE_MANY
            > - CrudMethods.PATCH_ONE
            > - CrudMethods.PATCH_MANY
            > - CrudMethods.UPSERT_ONE
            > - CrudMethods.UPSERT_MANY
            > - CrudMethods.DELETE_ONE
            > - CrudMethods.DELETE_MANY
            > - CrudMethods.POST_REDIRECT_GET

        - exclude_columns: `list` 
            > set the columns that not to be operated but the columns should nullable or set the default value)


5. use CrudRouter to register API
   ```python
    	crud_route = crud_router_builder(db_session=get_transaction_session,
                                          db_model=CRUDTest,
                                          crud_models=test_crud_model,
                                          async_mode = False,
                                          autocommit = False,
                                          prefix="/crud_test",
                                          dependencies = [],
                                          tags=["Example"]
                                          )
    ```
    - db_session: `execute session generator` 
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

    - db_model `SQLALchemy Declarative Base Class`
    
        >  **Note**: There are some constraint in the SQLALchemy Schema
    
    - async_mode`bool`: if your db session is async
    
        >  **Note**: require async session generator if True
    
    - autocommit`bool`: if you don't need to commit by your self    
    
        >  **Note**: require handle the commit in your async session generator if False
    
    - dependencies: API dependency injection of fastapi
        
        >  **Note**: Get the example usage in `./example`        

    - crud_models `sqlalchemy_to_pydantic` 

    - dynamic argument (prefix, tags): extra argument for APIRouter() of fastapi

    
   
6. Add to route and run
   
   ```
    import uvicorn
    from fastapi import FastAPI
   
    app = FastAPI()
    app.include_router(crud_route)
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
   ```


# Design

## Path Parameter

In the design of this tool, Path Parameters should be a primary key of table, that why limited primary key can only be one.

## Query Parameter

In `PUT` `DELETE` `PATCH`, user can use Path Parameters and Query Parameters to limit the scope of the data affected by the operation, and the Query Parameters is same with `FIND` API


- Query Operation will look like that when python type of column is 
  <details>
    <summary>string</summary>
  
    - **support Approximate String Matching that require this** 
        - (<column_name>____str, <column_name>____str_____matching_pattern)
    - **support In-place Operation, get the value of column in the list of input**
        - (<column_name>____list, <column_name>____list____comparison_operator)
    - **preview**
    ![string](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/string_query.png?raw=true)
  </details>
  
  <details>
    <summary>numeric or datetime</summary>
  
    - **support Range Searching from and to**
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - **support In-place Operation, get the value of column in the list of input**
        - (<column_name>____list, <column_name>____list____comparison_operator)
    - **preview**
        ![numeric](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/numeric_query.png?raw=true)
        ![datetime](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/time_query.png?raw=true)
  </details>

  <details>
    <summary>uuid</summary>
  
    uuid supports In-place Operation only
    - **support In-place Operation, get the value of column in the list of input**
        - (<column_name>____list, <column_name>____list____comparison_operator)
  </details>


- EXTRA query parameter for `GET_MANY`: 
  <details>
    <summary>Pagination</summary>
  
    - **limit**
    - **offset**
    - **order by**
    - **preview**
        ![Pagination](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/Pagination_query.png?raw=true)  

  </details>

    
### Query to SQL statement example

- [**Approximate String Matching**](https://www.postgresql.org/docs/9.3/functions-matching.html)
  <details>
    <summary>example</summary>
  
    - request url
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
  </details>

  
- **In-place Operation**
  <details>
    <summary>example</summary>
  
    - In-place support the following operation
    - generated sql if user select Equal operation and input True and False
    - preview
      ![in](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/in_query.png?raw=true)  

    - generated sql
      ```sql        
        select * FROM untitled_table_256 
        WHERE untitled_table_256.bool_value = true OR 
        untitled_table_256.bool_value = false
        ```  
    
  </details>        


- **Range Searching**
  <details>
    <summary>example</summary>
  
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
    
  </details>
  

- Also support your custom dependency for each api(there is a example in `./example`)


### Request Body

In the design of this tool, the columns of the table will be used as the fields of request body.

In the basic request body in the api generated by this tool, some fields are optional if :

* [x] it is primary key with autoincrement is True or the server_default or default is True
* [x] it is not a primary key, but the server_default or default is True
* [x] The field is nullable

## Upsert

POST API will perform the data insertion action with using the basic [Request Body](#request_body),
In addition, it also supports upsert(insert on conflict do)

The operation will use upsert instead if the unique column in the inserted row that is being inserted already exists in the table 

The tool uses unique columns in the table as a parameter of on conflict , and you can define which column will be updated 

![upsert](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/upsert_preview.png?raw=true)


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

- handle relationship
- support MYSQL and Sqllite
