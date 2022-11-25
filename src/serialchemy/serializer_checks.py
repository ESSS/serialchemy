from sqlalchemy import Column


def is_datetime_column(col):
    """
    Check if a column is DateTime (or implements DateTime)

    :param Column col: the column object to be checked

    :rtype: bool
    """
    from sqlalchemy import DateTime

    if not isinstance(col, Column):
        return False

    if hasattr(col.type, "impl"):
        return type(col.type.impl) is DateTime
    else:
        return type(col.type) is DateTime


def is_date_column(col):
    if not isinstance(col, Column):
        return False

    from sqlalchemy import Date

    return type(col.type) is Date


def is_enum_column(col):
    if not isinstance(col, Column):
        return False

    return hasattr(col.type, 'enum_class') and getattr(col.type, 'enum_class')
