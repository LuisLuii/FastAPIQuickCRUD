
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
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
- Refactor - Separate the sql parser 


### Fixed
 