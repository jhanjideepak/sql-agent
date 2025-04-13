from database.postgres_connector import get_postgres_connection
import json

def collect_feedback(query, sql_query, is_correct):
    """
    Collect user feedback and store it in PostgreSQL.
    """
    connection = get_postgres_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO feedback_query (query, sql_query, is_correct)
        VALUES (%s, %s, %s);
        """,
        (query, sql_query, is_correct)
    )
    connection.commit()
    cursor.close()