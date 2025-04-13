from database.postgres_connector import get_postgres_connection
import numpy as np
# from langchain.vectorstores.pgvector import PGVector
# from langchain.embeddings.openai import OpenAIEmbeddings
from config.postgres_config import POSTGRES_CONFIG

#
# # Initialize Langchain PGVector store
# vectorstore = PGVector(
#     collection_name="my_collection",
#     connection_string=f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['dbname']}",
#     embedding_function=None
# )

def store_vector(text, embedding):
    """
    Store a vector in PostgreSQL using pgvector.
    """
    connection = get_postgres_connection()
    cursor = connection.cursor()
    # ✅ Convert NumPy array to a Python list for PostgreSQL storage
    embedding_list = list(embedding)
    cursor.execute(
        "INSERT INTO vectors (text, embedding) VALUES (%s, %s);",
        (text, embedding_list)
    )
    connection.commit()
    # Insert into Langchain's 'langchain_pg_embedding'
    # vectorstore.add_embeddings([(text, embedding)])
    cursor.close()

def store_metadata_vectors(metadata, rag_model):
    """
    Generate embeddings for metadata and store them in PostgreSQL.
    """
    for table_name, columns in metadata.items():
        for col in columns:
            text = f"Table: {table_name}, Column: {col['column_name']}, Data Type: {col['data_type']}, Description: {col['description']}"
            embedding = rag_model.generate_embedding(text)
            store_vector(text=text, embedding=embedding)


def retrieve_vectors(query_embedding, top_k=3):
    """
    Retrieve vectors from both 'vectors' (custom) and 'langchain_pg_embedding'.
    """
    connection = get_postgres_connection()
    cursor = connection.cursor()

    try:
        # Retrieve from custom 'vectors' table
        cursor.execute("""
            SELECT text, embedding
            FROM vectors
            ORDER BY embedding <-> %s
            LIMIT %s;
        """, (np.array(query_embedding), top_k))

        custom_results = cursor.fetchall()

        # Retrieve from Langchain's PGVector
        # langchain_results = vectorstore.similarity_search_by_vector(query_embedding, k=top_k)

        # return {
        #     "custom_vectors": custom_results,
        #     "langchain_pg_embedding": langchain_results
        # }
        return custom_results

    except Exception as e:
        print(f"Error retrieving vectors: {e}")

    finally:
        cursor.close()
        connection.close()

def load_vectors():
    """
    Load all vectors from PostgreSQL into memory.
    """
    connection = get_postgres_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT text, embedding FROM vectors;")
    rows = cursor.fetchall()
    cursor.close()

    # Store vectors in a dictionary: {text: embedding}
    vectors = {row[0]: row[1] for row in rows}
    return vectors
