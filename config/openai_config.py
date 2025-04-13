import openai
from openai import OpenAI
import os

# Clear existing key
os.environ.pop("OPENAI_API_KEY", None)
# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "xxxxx"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# Initialize the OpenAI client
openai.api_key = OPENAI_API_KEY

def get_openai_client():
    """
    Return the OpenAI client.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client