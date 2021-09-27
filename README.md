#  FastAPI Quick CRUD

![Imgur](https://i.imgur.com/LsLKQHd.png)

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c2a6306f7f0a41948369d80368eb7abb?style=flat-square)](https://www.codacy.com/gh/LuisLuii/FastAPIQuickCRUD/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LuisLuii/FastAPIQuickCRUD&amp;utm_campaign=Badge_Grade)
[![Coverage Status](https://coveralls.io/repos/github/LuisLuii/FastAPIQuickCRUD/badge.svg?branch=main)](https://coveralls.io/github/LuisLuii/FastAPIQuickCRUD?branch=main)
[![CircleCI](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/main.svg?style=svg)](https://circleci.com/gh/LuisLuii/FastAPIQuickCRUD/tree/main)
[![PyPidownload](https://img.shields.io/pypi/dm/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)
[![SupportedVersion](https://img.shields.io/pypi/pyversions/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)
[![develop dtatus](https://img.shields.io/pypi/status/fastapi-quickcrud?style=flat-square)](https://pypi.org/project/fastapi-quickcrud)
[![PyPI version](https://badge.fury.io/py/fastapi-quickcrud.svg)](https://badge.fury.io/py/fastapi-quickcrud)


---






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
  - [Add description into docs](#add-description-into-docs)
  - [Relationship](#relationship)
  - [FastAPI_quickcrud Response Status Code standard](#fastapi_quickcrud-response-status-code-standard)
    


# Introduction

I believe that everyone who's working with FastApi and building some RESTful of CRUD services, wastes the time to writing similar code for simple CRUD every time

`FastAPI Quick CRUD` can generate CRUD in FastApi with SQLAlchemy schema 

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

![docs page](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/page_preview.png?raw=true)

## Advantage

  - [x] **Support SQLAlchemy 1.4** - Allow you build a fully asynchronous python service, also supports synchronization.
  
  - [x] **Full SQLAlchemy DBAPI Support** - Support different SQL for SQLAlchemy
    
  - [x] **Support Pagination** - `Get many` API support `order by` `offset` `limit` field in API

  - [x] **Rich FastAPI CRUD router generation** - Many operations of CRUD are implemented to complete the development and coverage of all aspects of basic CRUD.

  - [x] **CRUD route automatically generated** - Support Declarative class definitions and Imperative table
    
  - [x] **Flexible API request** - `UPDATE ONE/MANY` `FIND ONE/MANY` `PATCH ONE/MANY` `DELETE ONE/MANY` supports Path Parameters (primary key) and Query Parameters as a command to the resource to filter and limit the scope of the scope of data in request.
     
  - [x] **SQL Relationship** - `FIND ONE/MANY` supports Path get data with relationship
    
## Constraint
   
  - ❌ Alias is not support yet
  - ❌ If there are multiple **unique constraints**, please use **composite unique constraints** instead
  - ❌ **Composite primary key** is not support
  - ❌ Not Support API requests with specific resource `xxx/{primary key}` when table have not primary key; 
    - `UPDATE ONE`
    - `FIND ONE`
    - `PATCH ONE` 
    - `DELETE ONE` 
  

# Getting started

## Installation

```bash
pip install fastapi-quickcrud
```

## Usage

#### Simple Code (get more example from `./example`)

```python
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey, orm
from fastapi_quickcrud import crud_router_builder

Base = orm.declarative_base()


class User(Base):
    __tablename__ = 'test_users'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)


friend = Table(
    'test_friend', Base.metadata,
    Column('id', ForeignKey('test_users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend_name', String, nullable=False)
)

crud_route_1 = crud_router_builder(db_model=User,
                                   prefix="/user",
                                   tags=["User"],
                                   async_mode=True
                                   )
crud_route_2 = crud_router_builder(db_model=friend,
                                   prefix="/friend",
                                   tags=["friend"],
                                   async_mode=True
                                   )

app = FastAPI()
app.include_router(crud_route_1)
app.include_router(crud_route_2)
```

* Note:
 you can use [sqlacodegen](https://github.com/agronholm/sqlacodegen) to generate SQLAlchemy model for your table. This project is based on the model development and testing generated by sqlacodegen

### Main module

#### Generate CRUD router

**crud_router_builder args**
- db_session [Optional] `execute session generator` 
    - default using in-memory db with create table automatically
    - example:
        - sync SQLALchemy:
      ```python
        from sqlalchemy.orm import sessionmaker
        def get_transaction_session():
            try:
                db = sessionmaker(...)
                yield db
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
        ```
        - Async SQLALchemy
        ```python
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.ext.asyncio import AsyncSession
        async_session = sessionmaker(autocommit=False,
                             autoflush=False,
                             bind=engine,
                             class_=AsyncSession)

        async def get_transaction_session() -> AsyncSession:
            async with async_session() as session:
                async with session.begin():
                    yield session
        ```
- db_model [Require] `SQLALchemy Declarative Base Class or Table`
    
    >  **Note**: There are some constraint in the SQLALchemy Schema
    
- async_mode  [Optional (auto set by db_session)] `bool`: if your db session is async
    
    >  **Note**: require async session generator if True
    
- autocommit [Optional (default True)] `bool`: if you don't need to commit by your self    
    
    >  **Note**: require handle the commit in your async session generator if False
    
- dependencies [Optional]: API dependency injection of fastapi
        
    >  **Note**: Get the example usage in `./example`        

- crud_methods: ```CrudMethods```
    > - CrudMethods.FIND_ONE
    > - CrudMethods.FIND_MANY
    > - CrudMethods.UPDATE_ONE
    > - CrudMethods.UPDATE_MANY
    > - CrudMethods.PATCH_ONE
    > - CrudMethods.PATCH_MANY
    > - CrudMethods.UPSERT_ONE (only support postgresql yet)
    > - CrudMethods.UPSERT_MANY (only support postgresql yet)
    > - CrudMethods.CREATE_ONE
    > - CrudMethods.CREATE_MANY
    > - CrudMethods.DELETE_ONE
    > - CrudMethods.DELETE_MANY
    > - CrudMethods.POST_REDIRECT_GET

- exclude_columns: `list` 
  > set the columns that not to be operated but the columns should nullable or set the default value)


- dynamic argument (prefix, tags): extra argument for APIRouter() of fastapi


# Design

In `PUT` `DELETE` `PATCH`, user can use Path Parameters and Query Parameters to limit the scope of the data affected by the operation, and the Query Parameters is same with `FIND` API

## Path Parameter

In the design of this tool, **Path Parameters** should be a primary key of table, that why limited primary key can only be one.

## Query Parameter

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

* [x] it is primary key with `autoincrement` is True or the `server_default` or `default` is True
* [x] it is not a primary key, but the `server_default` or `default` is True
* [x] The field is nullable

## Upsert

** Upsert supports PosgreSQL only yet

POST API will perform the data insertion action with using the basic [Request Body](#request-body),
In addition, it also supports upsert(insert on conflict do)

The operation will use upsert instead if the unique column in the inserted row that is being inserted already exists in the table 

The tool uses `unique columns` in the table as a parameter of on conflict , and you can define which column will be updated 

![upsert](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/upsert_preview.png?raw=true)

## Add description into docs

You can declare `comment` argument for `sqlalchemy.Column` to configure the description of column

example:

```python

class Parent(Base):
    __tablename__ = 'parent_o2o'
    id = Column(Integer, primary_key=True,comment='parent_test')

    # one-to-many collection
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = 'child_o2o'
    id = Column(Integer, primary_key=True,comment='child_pk_test')
    parent_id = Column(Integer, ForeignKey('parent_o2o.id'),info=({'description':'child_parent_id_test'}))

    # many-to-one scalar
    parent = relationship("Parent", back_populates="children")
```


## Relationship

Now, `FIND_ONE` and `FIND_MANY` are supporting select data with join operation
```python

class Parent(Base):
    __tablename__ = 'parent_o2o'
    id = Column(Integer, primary_key=True)
    children = relationship("Child", back_populates="parent")

class Child(Base):
    __tablename__ = 'child_o2o'
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('parent_o2o.id'))
    parent = relationship("Parent", back_populates="children")
```
there is a relationship with using back_populates between Parent table and Child table, the `parent_id` in `Child` will refer to `id` column in `Parent`.

`FastApi Quick CRUD` will generate an api with a `join_foreign_table` field, and get api will respond to your selection of the reference data row of the corresponding table in `join_foreign_table` field, 

![join_1](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_preview_1.png?raw=true)

![join_2](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_preview_2.png?raw=true)

* Try Request
now there are some data in these two table
  
![parent](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_parent.png?raw=true)

![child](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_child.png?raw=true)

when i request
* Case One
    ```commandline
    curl -X 'GET' \
    'http://0.0.0.0:8000/parent?join_foreign_table=child_o2o' \
    -H 'accept: application/json'
    ```
    Response data
    ```json
    [
      {
        "id_foreign": [
          {
            "id": 1,
            "parent_id": 1
          },
          {
            "id": 2,
            "parent_id": 1
          }
        ],
        "id": 1
      },
      {
        "id_foreign": [
          {
            "id": 3,
            "parent_id": 2
          },
          {
            "id": 4,
            "parent_id": 2
          }
        ],
        "id": 2
      }
    ]
    ```
    Response headers
    ```text
     x-total-count: 4 
    ```
    
    There are response 4 data, response data will be grouped by the parent row, if the child refer to the same parent row
    
* Case Two
    ```commandline
    curl -X 'GET' \
    'http://0.0.0.0:8000/child?join_foreign_table=parent_o2o' \
    -H 'accept: application/json'
    ```
    Response data
    ```json
    [
      {
        "parent_id_foreign": [
          {
            "id": 1
          }
        ],
        "id": 1,
        "parent_id": 1
      },
      {
        "parent_id_foreign": [
          {
            "id": 1
          }
        ],
        "id": 2,
        "parent_id": 1
      },
      {
        "parent_id_foreign": [
          {
            "id": 2
          }
        ],
        "id": 3,
        "parent_id": 2
      },
      {
        "parent_id_foreign": [
          {
            "id": 2
          }
        ],
        "id": 4,
        "parent_id": 2
      }
    ]
    ```
    Response Header
    ```text
    x-total-count: 4 
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

- Upsert operation for each SQL
    

