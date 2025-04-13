# SQL Insight Bot with Milvus and Athena Integration

This project is a SQL Insight Bot that leverages **Milvus** for vector database operations, **Athena** for SQL query execution, and **Streamlit** for a user-friendly interface. The bot generates SQL queries from natural language inputs, executes them, and provides results while allowing user feedback for continuous improvement.

## Features

- **Natural Language to SQL Conversion**: Converts user queries into SQL statements.
- **Vector Database Integration**: Uses Milvus for efficient vector storage and retrieval.
- **Athena Query Execution**: Executes SQL queries on AWS Athena and retrieves results.
- **Feedback Mechanism**: Collects user feedback to improve query generation.
- **Caching**: Implements caching for frequently accessed data to improve performance.

## Project Structure

- `app.py`: Main Streamlit application for user interaction.
- `database/athena_connector.py`: Handles Athena query execution and table validation.
- `database/postgres_connector.py`: Manages PostgreSQL connections with `pgvector` support.
- `services/training_service.py`: Contains functions for training the Milvus vector database.
- `models/vanna_model.py`: Defines the Vanna AI model configuration.
- `config/`: Configuration files for Athena and PostgreSQL.

## Prerequisites

- Python 3.11+
- AWS credentials with permissions for Athena and S3.
- PostgreSQL with `pgvector` extension installed.
- Milvus vector database.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/sql-insight-bot.git
   cd sql-insight-bot