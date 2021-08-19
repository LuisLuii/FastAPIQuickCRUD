#  FastAPI Quick CRUD

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/c2a6306f7f0a41948369d80368eb7abb)](https://www.codacy.com/gh/LuisLuii/FastAPIQuickCRUD/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=LuisLuii/FastAPIQuickCRUD&amp;utm_campaign=Badge_Grade)


FastAPI Quick CRUD 可以為你節省編寫重複的CRUD代碼，用戶只需要為你的Postgresql table編寫Sqlalchemy Declarative Base Class 便可立即生成該Table的 CRUD API。

![docs page](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/page_preview.png?raw=true)

## 功能
- 把你的SQLALchemy Declarative Base Class 轉為CRUD routes, 支持以下crud method
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


## 安裝
```commandline
pip install fastapi-quickcrud
```

## 快速使用

1. 先建立你的SQLALchemy Declarative Base Class

    可以使用[sqlacodegen](https://pypi.org/project/sqlacodegen/)自動生成

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

2. 準備session

    ```python
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    def get_transaction_session():
        try:
            db = session()
            yield db
        finally:
            db.close()
    ```

3. import FastApi-quickcrud 的module

    ```python
    from fastapi_quickcrud import crud_router_builder
    from fastapi_quickcrud import CrudService
    from fastapi_quickcrud import CrudMethods
    from fastapi_quickcrud import sqlalchemy_to_pydantic
    ```

4. 轉換Sqlalchemy Schema 去 Pydantic model 以用作API 生成

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

    - 參數:
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

        - exclude_columns: 哪些columns 不想通過自動生成的API進行操作，但如果你生成insert data 相關的api 而該column 又不是nullable 或 有設置default value 便會出現錯誤
    
5. 使用CrudRouter生成 routes

    - db_session: `session 生成器` 
        - 例子:
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

    - async_mode: `bool` 如果session 是async
    
    - autocommit: `bool`  可以自已控制什麼時侯commit

    - crud_service: `CrudService`

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

## 設計

- 通過識別Column 的python 類型， FastAPI Quick CRUD 會生成以下的API 參數
  - string
    - 支持模糊搜索 
        - (<column_name>____str, <column_name>____str_____matching_pattern)
    - 支持 In-place搜索
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![string](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/string_query.png?raw=true)

  - numeric 
    - 支持範圍搜索
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - 支持 In-place搜索
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![numeric](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/numeric_query.png?raw=true)

  - datetime 
    - 支持範圍搜索
        - (<column_name>____from, <column_name>____from_____comparison_operator)
        - (<column_name>____to, <column_name>____to_____comparison_operator)
    - 支持 In-place搜索
        - (<column_name>____list, <column_name>____list____comparison_operator)
    
![datetime](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/time_query.png?raw=true)

  - 分頁 
    - limit
    - offset
    - order by
    
![Pagination](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/Pagination_query.png?raw=true)  

      
- 模糊搜索
    可以參考: https://www.postgresql.org/docs/9.3/functions-matching.html
    - 你query 會變成以下SQL statment:
      - query:
        
        ```text
          /test_CRUD?
          char_value____str_____matching_pattern=match_regex_with_case_sensitive&
          char_value____str_____matching_pattern=does_not_match_regex_with_case_insensitive&
          char_value____str_____matching_pattern=case_sensitive&
          char_value____str_____matching_pattern=not_case_insensitive&
          char_value____str=a&
          char_value____str=b
          ```
      - sql
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
      
- In-place 搜索
    - In-place 搜索支持以下圖中操作
    
![in](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/in_query.png?raw=true)  

    - query example
      - 如果用戶選擇Equal, 搜索True 和 False
```sql        
        select * FROM untitled_table_256 
        WHERE untitled_table_256.bool_value = true OR 
        untitled_table_256.bool_value = false
```     
        
- 範圍搜索
    - 範圍搜索支持以下圖中操作
    
![greater](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/greater_query.png?raw=true)  

    
![less](https://github.com/LuisLuii/FastAPIQuickCRUD/blob/main/pic/less_query.png?raw=true)  
 
  - 生成的SQL
    ```sql
    select * from untitled_table_256
    WHERE untitled_table_256.date_value > %(date_value_1)s 
    ```
    ```sql
    select * from untitled_table_256
    WHERE untitled_table_256.date_value < %(date_value_1)s 
    ```

FastAPI Quick CRUD 亦支持為船router加入dependency

# 限制

- 如果該table有多個unique column, 請使用composite unique constraint 
- 請勿同一時間使用composite unique constraint 和 單獨一個unique，除非該單獨的unique constraint己存在於composite unique constraint中
    ```python
        class Example(Base):
            __tablename__ = 'example'
            __table_args__ = (
                UniqueConstraint('p_id', 'test'),
            )
        
            p_id = Column(Integer, primary_key=True, unique=True)
            test = Column(Integer, unique=True)
            test_1 = Column(Text)

        ```

- Primary key是必要的，但不支持 composite primary key
- Query Field 會是可選輸入的，如果該column 有default value 或 nullable
- Sqlalchemy 的server_default的value不會顯示在OPENAPI，請使用default
- Query Field 是必須輸入的，如果如果該column 沒有default value 和 不是nullable
- Query暫不支持以下的Postgresql 的數據類型:
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

- 暫不支持Sqlalchemy 的 Automap() 

