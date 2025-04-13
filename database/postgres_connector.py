import psycopg2
from pgvector.psycopg2 import register_vector
from config.postgres_config import POSTGRES_CONFIG

def get_postgres_connection():
    """Create and return a PostgreSQL connection with pgvector support."""
    connection = psycopg2.connect(
        dbname=POSTGRES_CONFIG["dbname"],
        user=POSTGRES_CONFIG["user"],
        password=POSTGRES_CONFIG["password"],
        host=POSTGRES_CONFIG["host"],
        port=POSTGRES_CONFIG["port"],
    )
    register_vector(connection)  # Register pgvector support
    return connection