"""
vector_store.py
- 문서를 벡터화하여 FAISS DB에 저장
"""

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

def build_vector_store(docs, embedding_model: str):
    embeddings = OpenAIEmbeddings(model=embedding_model)
    return FAISS.from_documents(docs, embeddings)
