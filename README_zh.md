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

我相信很多人會使用FastAPI寫一些簡單CRUD服務，浪費時間去為每個table 寫高度相似的代碼

如果你是使用PostgreSQL,你便可以選擇`FastAPI Quick CRUD` 助你自動對每個table 生成以下的Routers
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

`FastAPI Quick CRUD`是基於SQLAlchemy `1.4.23` 版本進行開發，同時支持同步及異步

## 好處

  - [x] **支持 SQLAlchemy 1.41版本** - 允許你建立異步或同步的api 服務
  
  - [x] **支持分頁** - Get many API 支持 order by offset limit 

  - [x] **CRUD路由自動生成n** - 豐富的CRUD路由生成選擇 - 多種CRUD操作可供選擇

  - [x] **CRUD路由自動生成** - 支持SQLAlchemy的 Declarative class definitions 和 Imperative table
    
  - [x] **彈性API 請求** - `UPDATE ONE/MANY` `FIND ONE/MANY` `PATCH ONE/MANY` `DELETE ONE/MANY` 支持利用主鍵作為Path parameter and 以及table的column作Query Parameters，先對數據進行過濾再處理
    
## 限制
   
  - ❌ 只支持 PostgreSQL yet 
  - ❌ 請使用**composite unique constraints** 代替多個**unique constraints**
  - ❌ table 只能有一個主鍵
  - ❌ 以下API 不支持**Path Parameter** 如果沒有主鍵
    - `UPDATE ONE`
    - `FIND ONE`
    - `PATCH ONE` 
    - `DELETE ONE` 
  - ❌ [Alias](#alias) 只支持Declarative Base Model
  - ❌ 以下的類型未全面支持
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

# 使用

## 安裝

```bash
pip install fastapi-quickcrud
```

使用 PostgreSQL :
```bash
docker run -d -p 5432:5432 --name mypostgres --restart always -v postgresql-data:/var/lib/postgresql/data -e POSTGRES_PASSWORD=1234 postgres
```

#### 例子 (到 `./example` 取得更多例子)

```python
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from sqlalchemy import Column, Integer, \
    String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

from fastapi_quickcrud import CrudMethods
from fastapi_quickcrud import crud_router_builder
from fastapi_quickcrud import sqlalchemy_table_to_pydantic
from fastapi_quickcrud import sqlalchemy_to_pydantic

app = FastAPI()

Base = declarative_base()
metadata = Base.metadata

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine('postgresql+asyncpg://postgres:1234@127.0.0.1:5432/postgres', future=True, echo=True,
                             pool_use_lifo=True, pool_pre_ping=True, pool_recycle=7200)
async_session = sessionmaker(bind=engine, class_=AsyncSession)


async def get_transaction_session() -> AsyncSession:
    async with async_session() as session:
        async with session.begin():
            yield session


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, default=datetime.now(timezone.utc).strftime('%H:%M:%S%z'))


friend = Table(
    'friend', metadata,
    Column('id', ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False),
    Column('friend_name', String, nullable=False)
)

user_model_set = sqlalchemy_to_pydantic(db_model=User,
                                        crud_methods=[
                                            CrudMethods.FIND_MANY,
                                            CrudMethods.FIND_ONE,
                                            CrudMethods.UPSERT_ONE,
                                            CrudMethods.UPDATE_MANY,
                                            CrudMethods.UPDATE_ONE,
                                            CrudMethods.DELETE_ONE,
                                            CrudMethods.DELETE_MANY,
                                            CrudMethods.PATCH_MANY,

                                        ],
                                        exclude_columns=[])

friend_model_set = sqlalchemy_table_to_pydantic(db_model=friend,
                                                crud_methods=[
                                                    CrudMethods.FIND_MANY,
                                                    CrudMethods.UPSERT_MANY,
                                                    CrudMethods.UPDATE_MANY,
                                                    CrudMethods.DELETE_MANY,
                                                    CrudMethods.PATCH_MANY,

                                                ],
                                                exclude_columns=[])


crud_route_1 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=user_model_set,
                                   db_model=User,
                                   prefix="/user",
                                   dependencies=[],
                                   async_mode=True,
                                   tags=["User"]
                                   )
crud_route_2 = crud_router_builder(db_session=get_transaction_session,
                                   crud_models=friend_model_set,
                                   db_model=friend,
                                   async_mode=True,
                                   prefix="/friend",
                                   dependencies=[],
                                   tags=["Friend"]
                                   )


app.include_router(crud_route_1)
app.include_router(crud_route_2)
uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
```

### 主要模組

#### SQLAlchemy 的轉換


使用 **sqlalchemy_to_pydantic** 如果 SQLAlchemy model 是 Declarative Base Class

使用 **sqlalchemy_table_to_pydantic** 如果 SQLAlchemy model 是 Table


- 參數:
  - db_model: ```SQLALchemy Declarative Base Class or Table```
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
    > 設置哪些column不想通過API 操作，如果你要進行插入或更新，請注意該column一定要nullable 或有default value 以壓保不會出錯
    
----

#### 生成 CRUD 路由 模組

**crud_router_builder**
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
- db_model `SQLALchemy Declarative Base Class or Table`
    
    >  **Note**: 參考以上限制
    
- async_mode`bool`: if your db session is async
    
    >  **Note**: 如果connection 是async 請設定True
    
- autocommit`bool`: if you don't need to commit by your self    
    
    >  **Note**: require handle the commit in your async session generator if False
    
- dependencies: API dependency injection of fastapi
        
    >  **Note**: Get the example usage in `./example`        

- crud_models `sqlalchemy_to_pydantic` 

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

POST API will perform the data insertion action with using the basic [Request Body](#request-body),
In addition, it also supports upsert(insert on conflict do)

The operation will use upsert instead if the unique column in the inserted row that is being inserted already exists in the table 

The tool uses `unique columns` in the table as a parameter of on conflict , and you can define which column will be updated 

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
- support MYSQL , MSSQL cfand Sqllite
