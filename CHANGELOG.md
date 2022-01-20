
# Change Log
All notable changes to this project will be documented in this file.



## [not release] - 2021-09-27
 
### FIX
pydantic update is not good for this project

---

## [not release] - 2021-09-27
 
### Added
Full SQL support

### Changed


### Fixed

### ToDo

upsert for each sql
---


## [not release] - 2021-09-08
 
### Added
Field description in docs

### Changed


### Fixed


## [0.0.1a16] - 2021-09-08
 
### Added
relationship with get api

### Changed

disable alias

usage is more easy and quick build up

### Fixed


## [0.0.1a13] - 2021-08-23
 
### Added

### Changed

### Fixed

post redirect get can not rollback when find one api not found with async session

---

## [0.0.1a12] - 2021-08-23
 
### Added

support create more than one pydantic model with same

### Changed

### Fixed

duplicated pydantic model name 


---


## [Unreleased] - 2021-08-22
 
### Added

SQLAlchemy Table is supported, but not support alias yet

Support create CRUD route without primary key for SQLAlchemy Table 

```python

UntitledTable256 = Table(
    'test_table', metadata,
    Column('bool_value', Boolean, nullable=False, server_default=text("false")),
    Column('bytea_value', LargeBinary),
    Column('char_value', CHAR(10)),
    Column('date_value', Date, server_default=text("now()")),
    Column('float4_value', Float, nullable=False),
    Column('float8_value', Float(53), nullable=False, server_default=text("10.10")),
    Column('int2_value', SmallInteger, nullable=False),
    Column('int4_value', Integer, nullable=False),
    Column('int8_value', BigInteger, server_default=text("99")),
    Column('interval_value', INTERVAL),
    Column('json_value', JSON),
    Column('jsonb_value', JSONB(astext_type=Text())),
    Column('numeric_value', Numeric),
    Column('text_value', Text),
    Column('time_value', Time),
    Column('timestamp_value', DateTime),
    Column('timestamptz_value', DateTime(True)),
    Column('timetz_value', Time(True)),
    Column('uuid_value', UUID),
    Column('varchar_value', String),
    Column('array_value', ARRAY(Integer())),
    Column('array_str__value', ARRAY(String())),
    UniqueConstraint( 'int4_value', 'float4_value'),
)
```


### Changed
- primary key can be optional if autoincrement is True

- get many responses 204 if not found

### Fixed

---

##  - 2021-08-20
 
### Added
 
### Changed
- primary key will be required if no default value or not nullable


### Fixed

---

##  - 2021-08-19
 
### Added
- User don't need to declare crud_service



### Changed
- query abstract
    - Sqlalchemy
- route abstract
### Fixed

When you ask for a specific resource, say a user or with query param, and the user doesn't exist

 ```https://0.0.0.0:8080/api/:userid```
 
then fastapi-qucikcrud should return 404. In this case, the client requested a resource that doesn't exist.

----

In the other case, you have  an api that returns all users in the system using the following url:

 ```https://0.0.0.0:8080/api/user```

If there are no users in the system, then, in this case, you should return 204.


---

##  - 2021-08-18
 
### Added
 - FastAPIQuickCRUD support commit by user
  - for example if autocommit set False
    ```python
    def get_transaction_session():
        try:
            db = sync_session()
            yield db
        finally:
            db.commit()
            db.close()
    ```
  - for example if autocommit set True
    ```python
    def get_transaction_session():
        try:
            db = sync_session()
            yield db
        finally:
            db.close()
    ```
### Changed
- Refactor - Separate the sql result parsing


### Fixed
 