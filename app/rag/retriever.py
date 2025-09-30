"""
retriever.py : Azure Cognitive Search 기반 문서 검색
- 텍스트 임베딩을 생성 후, Azure AI Search에서 벡터+키워드 검색 수행
"""

import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from app.config import AppConfig
from openai import AzureOpenAI

logger = logging.getLogger("entraaid_app")


def search_top_k(query: str, top_k: int = 3):
    """
    Azure Cognitive Search에서 상위 K개 검색
    """
    try:
        # ✅ SearchClient 생성
        client = SearchClient(
            endpoint=AppConfig.AIS_ENDPOINT,
            index_name=AppConfig.AIS_INDEX,
            credential=AzureKeyCredential(AppConfig.AIS_API_KEY),
        )
        logger.info("SearchClient 생성 성공: index=%s", AppConfig.AIS_INDEX)

        # ✅ OpenAI 임베딩 생성
        if AppConfig.AOAI_ENDPOINT is None:
            logger.error("❌ AOAI_ENDPOINT가 None입니다. 올바른 엔드포인트를 설정하세요.")
            return []
        embedding_client = AzureOpenAI(
            azure_endpoint=AppConfig.AOAI_ENDPOINT,
            api_key=AppConfig.AOAI_API_KEY,
            api_version=AppConfig.AOAI_API_VERSION,
        )
        embedding_response = embedding_client.embeddings.create(
            model=AppConfig.AOAI_EMBED_DEPLOYMENT,
            input=query
        )
        vector = embedding_response.data[0].embedding
        logger.info("임베딩 생성 성공: 길이=%d", len(vector))

        # ✅ 최신 SDK에서는 vector_queries 사용
        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="text_vector"   # 인덱스의 벡터 필드명
        )

        # ✅ vector_queries + keyword 병합 검색
        results = client.search(
            search_text=query,  # 키워드 검색
            vector_queries=[vector_query],  # 벡터 검색
            select=["chunk_id", "parent_id", "chunk", "title", "content"],  # 필요한 필드만
            top=top_k
        )

        docs = []
        for doc in results:
            if not doc.get("chunk"):
                logger.warning("빈 컨텐츠 문서 스킵: id=%s", doc.get("chunk_id"))
                continue
            docs.append(doc)

        logger.info("검색 완료: query='%s' → %d건", query, len(docs))
        return docs

    except Exception as e:
        logger.error("❌ 검색 오류: %s", e, exc_info=True)
        return []
