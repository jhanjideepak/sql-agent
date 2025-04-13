from config.openai_config import get_openai_client
from vanna.base import VannaBase  # Import VannaBase
from vanna.openai import OpenAI_Chat
import logging
from pymilvus import MilvusClient, model
from vanna.milvus import Milvus_VectorStore
from vanna.openai import OpenAI_Chat

class VannaMilvus(Milvus_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        Milvus_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

class CustomVannaModel():
    def __init__(self, metadata=None, config=None):
        self.openai_client = get_openai_client()
        self.context = []
        
        # Create necessary directories
        self._setup_directories()
        
        # If metadata is provided, populate context
        if metadata:
            self.context = [
                f"Table: {table_name}\nColumns: {', '.join(col['column_name'] for col in columns)}"
                for table_name, columns in metadata.items()
            ]
            
        # Load previously trained tables
        self.trained_tables = set(self.get_trained_tables())
        
    def initialize(self):
        """Initialize the Vanna AI model."""
        logging.info("Vanna AI model initialized.")

    def _setup_directories(self):
        """Create necessary directories for storing training data."""
        import os
        os.makedirs("training_data", exist_ok=True)
        
        # Create empty files if they don't exist
        for filename in ["ddl_history.txt", "sql_history.txt", "doc_history.txt"]:
            filepath = os.path.join("training_data", filename)
            if not os.path.exists(filepath):
                with open(filepath, "w") as f:
                    pass

    def _append_to_file(self, filename, content):
        """Safely append content to a file in the training_data directory."""
        import os
        filepath = os.path.join("training_data", filename)
        with open(filepath, "a") as f:
            f.write(f"\n--- New Entry ---\n{content}\n")

    def train_with_metadata(self, metadata):
        """
        Train the model only if new metadata is detected.
        """
        new_tables = set(metadata.keys()) - self.trained_tables

        if not new_tables:
            logging.info("No new metadata to train. Skipping training.")
            return

        for table_name in new_tables:
            columns = metadata[table_name]
            ddl = f"CREATE TABLE {table_name} ("
            ddl += ", ".join([f"{col['column_name']} {col['data_type']}" for col in columns])
            ddl += ");"
            self.train(ddl=ddl, sql="sql")
            
            # Add to trained tables set
            self.trained_tables.add(table_name)

        # Save updated trained tables
        self.save_trained_tables(self.trained_tables)
        logging.info(f"Trained model with new tables: {new_tables}")

    def train(self, ddl=None, sql=None, documentation=None):
        """
        Train the model using DDL, SQL queries, or documentation.
        Also store training content for future reference.
        """
        if ddl:
            self._append_to_file("ddl_history.txt", ddl)
            prompt = f"""
            You are a SQL expert. Learn the following table schema:

            {ddl}
            """
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a SQL expert."},
                          {"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )

        if sql:
            self._append_to_file("sql_history.txt", sql)
            prompt = f"""
            You are a SQL expert. Learn the following SQL query:

            {sql}
            """
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a SQL expert."},
                          {"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )

        if documentation:
            self._append_to_file("doc_history.txt", documentation)
            prompt = f"""
            You are a SQL expert. Learn the following documentation:

            {documentation}
            """
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a SQL expert."},
                          {"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0
            )

    def get_trained_tables(self):
        """
        Retrieve a list of tables that have already been trained.
        """
        import os
        filepath = os.path.join("training_data", "trained_tables.txt")
        try:
            with open(filepath, "r") as f:
                return [table.strip() for table in f.read().splitlines() if table.strip()]
        except FileNotFoundError:
            return []

    def save_trained_tables(self, trained_tables):
        """
        Save the trained tables list to a file.
        """
        import os
        filepath = os.path.join("training_data", "trained_tables.txt")
        with open(filepath, "w") as f:
            f.write("\n".join(sorted(trained_tables)))

    def generate_sql(self, nl_query):
        """Generate SQL using stored context."""
        if not self.context:
            raise ValueError("No context available. Please add table context or train the model first.")

        context_str = "\n\n".join([
            "DATABASE CONTEXT: Table 'customer_level_data' captures aggregated customer-level insights by summarizing order-level details per common_customer_id. Each row represents a unique customer, with aggregated metrics such as total orders, total revenue",
            """DATABASE CONTEXT: Table 'order_level_data' captures order details at the job_id level, where each job_id represents a unique order. However, some details, such as vehicle-related information and quant_delivered, are captured at the individual vehicle level within each order\n
            Each order (job_id) can have multiple vehicles associated with it, but captured_amount, discount_amount, and promo_code are recorded at the order level and should not be double-counted when analyzing vehicle-level data. The dataset contains categorical, numerical, and datetime attributes that provide insights into the order process, customer details, service type, and fulfillment status.
            • Data Granularity: Most attributes are recorded at the job_id (order) level, except for vehicle-related details and quant_delivered, which are at the vehicle level within an order.
            • Revenue Calculation: Since captured_amount is recorded at the order level, it should not be double-counted when multiple vehicles exist under the same job_id.
            • Order Completion: Even if one item in an order is completed, the overall job_status is considered Completed"""
        ] + self.context + [
            "IMPORTANT RULES:",
            "1. Use only the tables and columns defined above",
            "2. Follow Amazon Athena SQL syntax",
            "3. Use proper date formats (YYYY-MM-DD)",
            "4. Include COUNT(DISTINCT ...) for counting unique records",
            "5. Always qualify column names with table names"
        ])

        prompt = (
            "You are an expert SQL developer specialized in Amazon Athena queries.\n\n"
            f"Available Database Information:\n{context_str}\n\n"
            f"User Question: {nl_query}\n\n"
            "Requirements:\n"
            "1. Generate a SQL query that precisely answers the user's question\n"
            "2. Only use tables and columns from the provided context\n"
            "3. Follow Amazon Athena SQL syntax requirements\n"
            "4. Include clear inline comments explaining the logic\n"
            "5. Qualify all column names with table names to avoid ambiguity\n\n"
            "6. Extract only the SQL query from the following text. Do not include any explanation, comments, or additional text. Provide only the clean SQL query in your response"
            "SQL Query:"
        )

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a SQL expert specialized in Amazon Athena query generation."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0
        )
        
        return response.choices[0].message.content.strip()

    def ask(self, question):
        print(f"Processing question: {question}")
        sql_query = self.generate_sql(question)
        print(f"Generated SQL: {sql_query}")
        return sql_query