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


# Introduction

我相信很多人會使用FastAPI寫一些簡單CRUD服務，浪費時間去為每個table 寫高度相似的代碼

如果你使用SQLAlchemy , 你可以通過`FastAPI Quick CRUD` 去生成CRUD API

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

`FastAPI Quick CRUD`是基於SQLAlchemy `1.4` 版本進行開發，同時支持同步及異步
![docs page](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/page_preview.png?raw=true)


## 好處

  - [x] **支持 SQLAlchemy 1.41版本** - 允許你建立異步或同步的api 服務
  
  - [x] **支持分頁** - Get many API 支持 order by offset limit 

  - [x] **支持全部SQL DBAPI ** - 支持所有SQLAlchemy 支持的SQL DB dialect

  - [x] **CRUD路由自動生成n** - 豐富的CRUD路由生成選擇 - 多種CRUD操作可供選擇

  - [x] **CRUD路由自動生成** - 支持SQLAlchemy的 Declarative class definitions 和 Imperative table
    
  - [x] **彈性API 請求** - `UPDATE ONE/MANY` `FIND ONE/MANY` `PATCH ONE/MANY` `DELETE ONE/MANY` 支持利用主鍵作為Path parameter and 以及table的column作Query Parameters，先對數據進行過濾再處理
    
## 限制
   
  - ❌ 請使用**composite unique constraints** 代替多個**unique constraints**
  - ❌ table 只能有一個主鍵
  - ❌ 以下API 不支持*Path Parameter* 如果沒有主鍵
    - `UPDATE ONE`
    - `FIND ONE`
    - `PATCH ONE` 
    - `DELETE ONE` 
  

# Getting started

## Installation

```bash
pip install fastapi-quickcrud
```


#### Simple Code (到 `./example` 取得更多例子)

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


### Main module

#### Generate CRUD router

**crud_router_builder args**
- db_session [Optional] `execute session generator` 
    - 默認使用In-memory DB, 或如以下例子自定義你的數據庫連接
    - example:
        - 同步 SQLALchemy:
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
        - 異步 SQLALchemy
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
    
    >  **Note**: db_model 會有一些限制，例如數據庫獨特的數據類型
    
- async_mode  [Optional (會通過你的db_session自動判斷)] `bool`: 你的數據庫連接是不是異步
    
    >  **Note**: 如果你的數據庫連接是異步，請設置True
    
- autocommit [Optional (default True)] `bool`: 自動幫你commit每一個 CRUD
    
    >  **Note**: 如果你在你的db_session 自已handle 了commit, 請設置False
  
- dependencies [Optional]: FastAPI 的依赖注入 
        
    >  **Note**:  `./example` 有相關使用例子        

- crud_methods [Optional]: ```CrudMethods``` 目前支持的CRUD， 如不設置便會自動設置
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

- exclude_columns: `list`1 
  > 怱略column，不會生成該怱略column的API請求列

- dynamic argument (prefix, tags): 用作FastApi APIRouter() 的參數



# Design

In `PUT` `DELETE` `PATCH`, 用戶可以通過 Path Parameters and Query Parameters 去限制受影響的數據 ，當中的Query Parameter 跟 `FIND` API一樣

## Path Parameter

在這個工具的設計中，**Path Parameters** 應該是表的一個主鍵，所以有限的主鍵只能是一個。

## Query Parameter

- 當列的 python 類型為時，查詢操作將如下所示
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


- `GET_MANY` 的額外查詢參數：
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
  

- 還支持您對每個 api 的自定義依賴項(there is a example in `./example`)

### 請求正文

在這個工具的設計中，表格的列將被用作請求正文的字段。

在此工俱生成的 api 中的基本請求正文中，某些字段是可選的，如果：

* [x] 它是主鍵，`autoincrement` 為 True 或 `server_default` 或 `default` 為 True
* [x] 它不是主鍵，但 `server_default` 或 `default` 為 True
* [x] 該字段可以為空

## Upsert
** Upsert 目前僅支持 PosgreSQL

POST API 將使用基本的 [Request Body](#request-body) 執行數據插入操作，
此外，它還支持upsert（在衝突時插入）

如果要插入的插入行中的唯一列已存在於表中，則該操作將使用 upsert

該工具使用表中的“唯一列”作為衝突時的參數，您可以定義將更新哪一列
![upsert](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/upsert_preview.png?raw=true)

## Add description into docs

你可以為`sqlalchemy.Column`聲明`comment`參數來配置列的描述

例子：

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

現在，`FIND_ONE` 和 `FIND_MANY` 支持 relationship
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
父表和子表之間使用back_populates有關係，`Child`中的`parent_id`將引用`Parent`中的`id`列。

`FastApi Quick CRUD`會生成一個帶有`join_foreign_table`字段的api，get api會響應你在`join_foreign_table`字段中選擇對應表的引用數據行，
![join_1](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_preview_1.png?raw=true)

![join_2](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_preview_2.png?raw=true)

* Try Request

現在這兩個表中有一些數據
  
![parent](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_parent.png?raw=true)

![child](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/join_child.png?raw=true)

當我請求時
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
    
    這有響應四個數據，響應數據將按父行分組，如果子引用相同的父行
    
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


當您請求特定資源時，例如一個用戶或帶有查詢參數，而該用戶不存在

 ```GET: get one : https://0.0.0.0:8080/api/:userid?xx=xx```

 ```UPDATE: update one : https://0.0.0.0:8080/api/:userid?xx=xx```

 ```PATCH: patch one : https://0.0.0.0:8080/api/:userid?xx=xx```

 ```DELETE: delete one : https://0.0.0.0:8080/api/:userid?xx=xx```

 
那麼 fastapi-qucikcrud 應該返回 404。在這種情況下，客戶端請求了一個不存在的資源。

----

在另一種情況下，您有一個 api，它使用以下 url 在系統中批量操作數據：

 ```GET: get many : https://0.0.0.0:8080/api/user?xx=xx```

 ```UPDATE: update many : https://0.0.0.0:8080/api/user?xx=xx```

 ```DELETE: delete many : https://0.0.0.0:8080/api/user?xx=xx```

 ```PATCH: patch many : https://0.0.0.0:8080/api/user?xx=xx```

如果系統中沒有用戶，那麼在這種情況下，您應該返回 204。

### TODO

- 每個 SQL 的 Upsert 操作
    

