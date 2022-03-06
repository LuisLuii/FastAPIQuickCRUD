from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.sql.schema import Table


def convert_table_to_model(db_model):
    NO_PRIMARY_KEY = False
    if not isinstance(db_model, Table):
        return db_model, NO_PRIMARY_KEY
    db_name = str(db_model.fullname)
    table_dict = {'__table__': db_model,
                  '__tablename__': db_name}

    if not db_model.primary_key:
        table_dict['__mapper_args__'] = {
            "primary_key": [i for i in db_model._columns]
        }
        NO_PRIMARY_KEY = True

    for i in db_model.c:
        col, = i.expression.base_columns
        table_dict[str(i.key)] = col

    return type(f'{db_name}DeclarativeBaseClass', (declarative_base(),), table_dict), NO_PRIMARY_KEY
