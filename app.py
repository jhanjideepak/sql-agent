import streamlit as st
from models.vanna_model import CustomVannaModel
from models.rag_model import RAGModel
from services.query_service import execute_query, generate_follow_up_questions
from services.metadata_service import load_metadata
from services.vector_service import store_metadata_vectors, load_vectors
from services.feedback_service import collect_feedback
import pandas as pd
from pymilvus import MilvusClient, model, connections
from models.vanna_model import CustomVannaModel, VannaMilvus
import os
# from st_milvus_connection import MilvusConnection

# connections.connect(alias="default", host="localhost", port="19530")
# print(connections.has_connection(alias="default"))


os.environ["milvus_uri"] = "./milvus_vanna.db"
milvus_uri = "./milvus_vanna.db"
# os.environ["milvus_token"] = "root:Milvus"
milvus_client = MilvusClient(uri=milvus_uri)

# ✅ Check if a connection already exists before reconnecting
# if "default" not in connections.list_connections():
#     connections.connect(alias="default", host="localhost", port="19530")
#
#
# conn = st.connection("milvus", type=MilvusConnection)

# Configure the app title
st.title("SQL Insight Bot")

# Initialize Vanna AI and RAG
# vanna_model = CustomVannaModel()

# Initialize Milvus client
# connections.connect(alias="default", host="localhost", port="8501")

# ✅ Initialize Vanna AI (only once)
vn_milvus = VannaMilvus(
    config={
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o",
        "milvus_client": milvus_client,
        "embedding_function": model.DefaultEmbeddingFunction(),
        "n_results": 5,
    }
)


# Load metadata
# metadata = load_metadata()

# Load precomputed embeddings
# vectors = load_vectors()
# rag_model = RAGModel()

# Train Vanna AI with metadata
# vanna_model.train_with_metadata(metadata)

# Input: Natural language query
nl_query = st.text_input("Enter your natural language query:", "Show number of grocery orders on 1st Feb 2025")

load = st.button("Generate SQL and Execute")
# Button: Generate SQL and execute query
# if st.button("Generate SQL and Execute"):
if "load_state" not in st.session_state:
    st.session_state.load_state = False

if load or st.session_state.load_state:
    st.session_state.load_state = True
    # Generate SQL from natural language query
    sql_query = vn_milvus.generate_sql(nl_query)
    st.write(f"Generated SQL: `{sql_query}`")

    # Execute SQL query using Athena
    try:
        result_df = execute_query(sql_query)
        st.write("Query Result:")
        st.dataframe(result_df)

        # # Generate follow-up questions
        # follow_up_questions = generate_follow_up_questions(result_df, metadata)
        # st.write("Follow-up Questions:")
        # for question in follow_up_questions:
        #     st.write(f"- {question}")

        # Function to collect feedback
        # Function to handle feedback updates
        def update_feedback():
            st.session_state["feedback"] = st.session_state["radio_feedback"]


        # Ensure session state is initialized
        if "feedback" not in st.session_state:
            st.session_state["feedback"] = None

        if "radio_feedback" not in st.session_state:
            st.session_state["radio_feedback"] = None  # No selection initially

        # Collect user feedback
        feedback = st.radio(label="Was the query correct?",
                            options=["Yes", "No"],
                            index=0 if st.session_state["feedback"] == "Yes" else (1 if st.session_state["feedback"] == "No" else None),
                            key="radio_feedback",
                            on_change=update_feedback)

        print(feedback)
        if st.session_state.get("feedback") is not None:
            is_correct = st.session_state["feedback"] == "Yes"
            st.write(f"Selected: {feedback}, is_correct: {is_correct}")
            if is_correct is True:
                collect_feedback(nl_query, sql_query, is_correct)
                st.write("Thank you for your feedback!")
            else:
                collect_feedback(nl_query, sql_query, is_correct)
                st.write("Thank you for your feedback. Our team will fix this")
    except Exception as e:
        st.error(f"Error executing query: {e}")