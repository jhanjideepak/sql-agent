from database.postgres_connector import get_postgres_connection

def load_metadata():
    """
    Load metadata from PostgreSQL.
    """
    connection = get_postgres_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT table_name, column_name, data_type, description FROM table_metadata;")
    rows = cursor.fetchall()
    cursor.close()

    metadata = {}
    for row in rows:
        table_name, column_name, data_type, description = row
        if table_name not in metadata:
            metadata[table_name] = []
        metadata[table_name].append({
            "column_name": column_name,
            "data_type": data_type,
            "description": description
        })
    return metadata

def load_sql_answer():
    connection = get_postgres_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT query, sql_query FROM feedback_query where is_correct = True;")
    rows = cursor.fetchall()
    return rows