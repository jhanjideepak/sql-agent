from models.vanna_model import CustomVannaModel, VannaMilvus
# from models.rag_model import RAGModel
from services.query_service import execute_query, generate_follow_up_questions
from services.metadata_service import load_metadata
from services.vector_service import store_metadata_vectors
from services.feedback_service import collect_feedback
from database.athena_connector import validate_tables
from services.training_service import train_milvus_vanna
import logging
import pandas as pd
from pymilvus import MilvusClient, model
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

milvus_uri = "./milvus_vanna.db"

milvus_client = MilvusClient(uri=milvus_uri)

def main():

    logging.info("Loading metadata...")
    # Here metadata is DDL
    metadata = load_metadata()
    logging.info(f"Loaded Metadata: {metadata}")

    logging.info("Initializing Vanna AI and RAG...")
    milvus_client = MilvusClient(uri=milvus_uri)

    # Initialize Vanna AI with Milvus
    vn_milvus = VannaMilvus(
        config={
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-4o",
            "milvus_client": milvus_client,
            "embedding_function": model.DefaultEmbeddingFunction(),
            "n_results": 5,  # Number of results to return from Milvus semantic search
        }
    )


    # Path to the file containing SQL queries
    query_file_path = "./training_data/sql_history.txt"  # Update with the actual file path
    doc_file_path = "./training_data/doc_history.txt"

    train_milvus_vanna(vn_milvus, metadata, query_file_path, doc_file_path)

    # training_data = vn_milvus.get_training_data()
    nl_query = "Show top 3 performing grocery pilots in last 7 days"
    sql_query = vn_milvus.generate_sql(nl_query)
    # vn_milvus.run_sql(sql)

    # Define a custom list of tables
    custom_tables = ['insight_bot_order_level_data', 'insight_bot_customer_level_data']

    logging.info("Validating custom tables...")
    try:
        valid_tables = validate_tables(custom_tables, database="cafu_temp")
        logging.info(f"Valid tables: {valid_tables}")
    except ValueError as e:
        logging.error(e)
        return

    logging.info("Generating SQL from natural language query...")
    # nl_query = "Show number of orders on 1st Feb 2025"
    # sql_query = vanna_model.generate_sql(nl_query)
    # sql_query = vanna_model.ask(nl_query)

    logging.info(f"Generated SQL: {sql_query}")

    logging.info("Executing SQL query using Athena...")
    try:
        result_df = execute_query(sql_query)
        logging.info(f"Query Result: {result_df}")
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        result_df = pd.DataFrame()  # Fallback to empty DataFrame

    # logging.info("Executing SQL query using Athena...")
    # result_df = execute_query(sql_query)
    # logging.info(f"Query Result: {result_df}")

    # logging.info("Generating follow-up questions...")
    # follow_up_questions = generate_follow_up_questions(result_df, metadata)
    # logging.info("Follow-up Questions:")
    # for question in follow_up_questions:
    #     logging.info(f"- {question}")

    logging.info("Collecting user feedback...")
    feedback = input("Was the query correct? (yes/no): ").strip().lower()
    # Collect user feedback
    if feedback:
        is_correct = feedback == "yes"
        if is_correct is True:
            collect_feedback(nl_query, sql_query, is_correct)
            print("Thank you for your feedback!")
        else:
            collect_feedback(nl_query, sql_query, is_correct)
            print("Thank you for your feedback. Our team will fix this")


if __name__ == "__main__":
    main()