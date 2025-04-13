import pandas as pd
from database.athena_connector import query_athena

def execute_query(sql_query):
    """
    Execute a SQL query on Athena and return the result as a DataFrame.
    """
    return query_athena(sql_query)

def generate_follow_up_questions(result_df, metadata):
    """
    Generate follow-up questions based on the query results and metadata.
    """
    follow_up_questions = []

    # Example: Suggest aggregations if the result is large
    if len(result_df) > 10:
        follow_up_questions.append("Can you show me the average age of users?")
        follow_up_questions.append("Can you group the results by name?")

    # Example: Suggest filtering based on metadata
    for column in result_df.columns:
        if column in metadata.get("users", {}):
            follow_up_questions.append(f"Can you filter the results by {column}?")

    return follow_up_questions