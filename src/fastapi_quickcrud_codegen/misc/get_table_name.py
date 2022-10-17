from sqlalchemy import Table


def get_table_name_from_table(table):
    return table.name


def get_table_name_from_model(table):
    return table.__tablename__


def get_table_name(table):
    if isinstance(table, Table):
        return get_table_name_from_table(table)
    else:
        return get_table_name_from_model(table)