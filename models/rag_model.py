from config.openai_config import get_openai_client
from services.vector_service import store_vector, retrieve_vectors
import numpy as np

class RAGModel:
    def __init__(self):
        self.openai_client = get_openai_client()
        self.vector_dim = 1536  # OpenAI embeddings have 1536 dimensions

    def generate_embedding(self, text):
        """
        Generate an embedding for the given text using OpenAI.
        """
        response = self.openai_client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def retrieve_context(self, query_text, top_k=3):
        """
        Retrieve the most relevant context for a query using OpenAI embeddings.
        """
        query_embedding = self.generate_embedding(query_text)
        # Retrieve top-k similar vectors from PostgreSQL
        return retrieve_vectors(query_embedding, top_k=top_k)

    def cosine_similarity(self, vec1, vec2):
        """
        Compute cosine similarity between two vectors.
        """
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))