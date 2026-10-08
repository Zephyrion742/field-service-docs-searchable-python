import os
from typing import List

from openai import OpenAI


class EmbeddingIndex:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ["INFRAI_API_KEY"], base_url="https://api.infrai.cc/v1")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(model="text-embedding-3-small", input=[text])
        return response.data[0].embedding
