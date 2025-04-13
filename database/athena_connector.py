import boto3
from config.athena_config import ATHENA_CONFIG
import time
import pandas as pd

# Create a boto3 session
# my_session = boto3.Session(
#     region_name=ATHENA_CONFIG["region_name"]
#     # profile_name="de-ro" # Use your profile name
# )

# IAM Role to Assume
ROLE_ARN = "arn:aws:iam::8006XXXXXXXX:role/SA-SQL-INSIGHT-BOT"


def assume_role(role_arn):
    """
    Assume the given IAM role and return temporary credentials.
    """
    sts_client = boto3.client("sts")
    assumed_role = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="AthenaQuerySession"
    )
    credentials = assumed_role["Credentials"]

    return credentials

credentials = assume_role(ROLE_ARN)

my_session = boto3.Session(
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"],
    region_name=ATHENA_CONFIG["region_name"]
)

def get_athena_client():
    """
    Create and return a boto3 Athena client.
    """
    return my_session.client("athena")

def validate_tables(custom_tables, database="db_temp"):
    """
    Validate if the custom tables exist in the specified Athena database.
    Handles pagination to retrieve all tables.
    
    Args:
        custom_tables (list): List of table names to validate
        database (str): Name of the Athena database
        
    Returns:
        list: List of validated table names
        
    Raises:
        ValueError: If any specified tables don't exist in the database
    """
    athena_client = get_athena_client()
    existing_table_names = []
    
    # Initialize pagination token
    pagination_token = None
    
    try:
        while True:
            # Prepare the base request
            request = {
                'CatalogName': 'AwsDataCatalog',
                'DatabaseName': database
            }
            
            # Add pagination token if it exists
            if pagination_token:
                request['NextToken'] = pagination_token
            
            # Get batch of tables
            response = athena_client.list_table_metadata(**request)
            
            # Add table names from current batch
            existing_table_names.extend([
                table['Name'] for table in response['TableMetadataList']
            ])
            
            # Check if there are more tables to fetch
            pagination_token = response.get('NextToken')
            if not pagination_token:
                break
                
        print(f"Found {len(existing_table_names)} tables in database")
        # print(f"Existing tables: {existing_table_names}")
        
        # Check if custom tables exist in the database
        invalid_tables = [
            table for table in custom_tables 
            if table not in existing_table_names
        ]
        
        if invalid_tables:
            raise ValueError(
                f"The following tables do not exist in the database: {invalid_tables}"
            )
        
        return custom_tables
        
    except Exception as e:
        if 'DatabaseNotFoundError' in str(e):
            raise ValueError(f"Database '{database}' not found")
        elif 'AccessDeniedException' in str(e):
            raise ValueError("Insufficient permissions to access Athena metadata")
        else:
            raise ValueError(f"Error validating tables: {str(e)}")

def query_athena(sql_query):
    """
    Execute a SQL query on Athena and return the result as a DataFrame.
    """
    # Initialize Athena client
    athena_client = get_athena_client()

    # Start query execution
    response = athena_client.start_query_execution(
        QueryString=sql_query,
        QueryExecutionContext={
            "Database": "db_temp"
        },
        ResultConfiguration={
            "OutputLocation": ATHENA_CONFIG["s3_staging_dir"]
        }
    )

    # Get QueryExecutionId
    query_execution_id = response["QueryExecutionId"]

    # Wait for the query to complete
    while True:
        response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
        status = response["QueryExecution"]["Status"]["State"]
        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            break
        time.sleep(1)  # Wait for 1 second before checking again

    # Check if the query succeeded
    if status != "SUCCEEDED":
        failure_reason = response["QueryExecution"]["Status"].get("StateChangeReason", "Unknown error")
        print(f"QueryExecutionId: {query_execution_id}")
        print(f"Query failed. Reason: {failure_reason}")
        raise Exception(f"Query failed with status: {status}. Reason: {failure_reason}")

    # Fetch query results
    results = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    print(results)

    # Convert results to a DataFrame
    rows = results["ResultSet"]["Rows"]
    # columns = [col["Name"] for col in rows[0]["Data"]]
    columns = [col.get("VarCharValue", "Unknown") for col in rows[0]["Data"]]
    data = []
    for row in rows[1:]:
        data.append([cell.get("VarCharValue", None) for cell in row["Data"]])
    return pd.DataFrame(data, columns=columns)