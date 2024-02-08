import pymysql
from flask import current_app


def connect_db():
    connection = pymysql.connect(
        host=current_app.config['MYSQL_HOST'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        db=current_app.config['MYSQL_DB'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor)
    return connection


def avg_type_size(vessel_type):
    connection = connect_db()
    table_name = current_app.config['REALTIME_TABLE']
    with connection.cursor() as cursor:
        if vessel_type:
            query = f"""
                    SELECT avg(length) as length, avg(width) as width, avg(sog) as sog
                    FROM `{table_name}` 
                    WHERE vessel_type = %s and length != 0 and width != 0
                    """
            cursor.execute(query, (vessel_type,))
        else:
            query = f"""
                    SELECT avg(length) as length, avg(width) as width, avg(sog) as sog
                    FROM `{table_name}` 
                    WHERE length != 0 and width != 0
                    """
            cursor.execute(query)
        results_avg = cursor.fetchone()

        if results_avg:
            avg_length, avg_width, avg_sog = results_avg["length"], results_avg["width"], results_avg["sog"]
    connection.close()
    return avg_length, avg_width, avg_sog
