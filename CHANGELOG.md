
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - 2021-08-20
 
### Added
 
### Changed
- primary key will be required if no default value or not nullable


### Fixed


## [Unreleased] - 2021-08-19
 
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


## [Unreleased] - 2021-08-18
 
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
 