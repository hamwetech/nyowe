from django.db import connection, IntegrityError


def dict_fetch_all(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def execute_sql(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        result = dict_fetch_all(cursor)
    return result
