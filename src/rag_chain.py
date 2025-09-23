"""
rag_chain.py
- LLM + 벡터DB를 연결하는 RAG 체인 (출처 포함)
"""

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain

def create_rag_chain_with_sources(llm_model: str, db, k: int = 3, temperature: float = 0):
    llm = ChatOpenAI(model=llm_model, temperature=temperature)
    return RetrievalQAWithSourcesChain.from_chain_type(
        llm,
        retriever=db.as_retriever(search_type="similarity", search_kwargs={"k": k}),
    )
