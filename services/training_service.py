import vanna as vn
from pymilvus import MilvusClient, model
import logging
from services.metadata_service import  load_sql_answer
from models.vanna_model import VannaMilvus
import os
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def train_vanna(ddl=None, sql_queries=None, documentation=None):
    """
    Train Vanna AI on the database schema and example queries.

    Args:
        ddl (str): DDL statements for the database schema.
        sql_queries (list): List of SQL queries for training.
        documentation (str): Documentation for the database.
    """
    if ddl:
        vn.train(ddl=ddl)
    if sql_queries:
        for sql in sql_queries:
            vn.train(sql=sql)
    if documentation:
        vn.train(documentation=documentation)


def train_milvus_vanna(vn_milvus, metadata, query_file_path, doc_file_path):
    """
    Train Vanna AI with metadata and historical SQL queries.

    Args:
        metadata (dict): Table metadata to train Vanna AI.
        milvus_client (MilvusClient): Milvus database client.
        query_file_path (str): Path to the file containing SQL queries.

    Returns:
        None
    """

    # Initialize Vanna AI with Milvus
    # vn_milvus = VannaMilvus(
    #     config={
    #         "api_key": os.getenv("OPENAI_API_KEY"),
    #         "model": "gpt-4o",
    #         "milvus_client": milvus_client,
    #         "embedding_function": model.DefaultEmbeddingFunction(),
    #         "n_results": 5,  # Number of results to return from Milvus semantic search
    #     }
    # )

    logging.info("Training Vanna AI with metadata...")

    # Get new tables from metadata
    new_tables = set(metadata.keys())

    if not new_tables:
        logging.info("No new metadata to train. Skipping training.")
        return

    # Train with table metadata
    for table_name in new_tables:
        columns = metadata[table_name]
        ddl = f"CREATE TABLE {table_name} ("
        ddl += ", ".join([f"{col['column_name']} {col['data_type']}" for col in columns])
        ddl += ");"
        vn_milvus.train(ddl=ddl)

    logging.info("Metadata training completed.")

    # Read and execute historical queries
    queries = read_queries_from_file(query_file_path)

    for query in queries:
        try:
            vn_milvus.train(sql=query)  # Execute training on SQL queries
            logging.info(f"Executed query:\n{query}\n")
        except Exception as e:
            logging.error(f"Error executing query:\n{query}\nError: {e}")

    # Train documentation
    documentation = read_documentation(doc_file_path)
    vn_milvus.train(documentation=documentation)

    # Train using question - sql pair
    # cursor.execute("SELECT query, sql_query FROM feedback_query where is_correct = True")  # Replace `training_data` with your table name
    # rows = cursor.fetchall()  # Returns a list of tuples (question, sql_query)
    rows = load_sql_answer()
    # Loop through each question-SQL pair and train Vanna AI
    for question, sql in rows:
        try:
            vn_milvus.train(question=question, sql=sql)
            print(f"Trained: {question}")
        except Exception as e:
            print(f"Error training {question}: {e}")


def read_queries_from_file(file_path):
    """
    Reads SQL queries from a file.

    Args:
        file_path (str): Path to the SQL file.

    Returns:
        list: List of SQL queries.
    """
    try:
        with open(file_path, 'r') as file:
            queries = file.read().strip().split(";")  # Split by semicolon
            return [query.strip() for query in queries if query.strip()]  # Remove empty queries
    except Exception as e:
        logging.error(f"Error reading query file: {e}")
        return []

def read_documentation(file_path):
    """
    Reads the full content of a documentation file.

    Args:
        file_path (str): Path to the text file.

    Returns:
        str: The full content of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except Exception as e:
        logging.error(f"Error reading documentation file: {e}")
        return None