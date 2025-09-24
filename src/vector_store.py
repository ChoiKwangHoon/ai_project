"""
vector_store.py
- 문서를 벡터화하여 FAISS DB에 저장 (AzureOpenAIEmbeddings 사용)
"""

import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def build_vector_store(docs, embedding_model: str):
    """
    주어진 문서를 Azure OpenAI Embeddings 으로 벡터화하고
    FAISS 벡터스토어에 저장
    """
    embeddings = AzureOpenAIEmbeddings(
        model=embedding_model,
        azure_deployment=os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "embedding-deployment"),
        openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    return FAISS.from_documents(docs, embeddings)
