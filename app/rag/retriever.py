"""
retriever.py : Azure Cognitive Search 기반 문서 검색
- Azure AI Search와 Azure OpenAI 임베딩을 활용해 하이브리드 검색을 수행한다.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, cast

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

from app.config import AppConfig

logger = logging.getLogger("entraaid_app")


_search_client: Optional[SearchClient] = None
_embedding_client: Optional[AzureOpenAI] = None


_COMPOUND_REPLACEMENTS: List[tuple[str, str]] = [
    ("entraapp신청가이드", "entraapp 신청 가이드"),
    ("entraapp신청", "entraapp 신청"),
    ("entraapp가이드", "entraapp 가이드"),
    ("신청가이드", "신청 가이드"),
]

_SYNONYM_MAP: Dict[str, List[str]] = {
    "entraapp": ["entra app", "entra id app", "엔트라앱"],
    "entra": ["엔트라", "entra id"],
    "신청": ["등록", "신청서", "apply", "application"],
    "가이드": ["안내", "guide", "매뉴얼", "documentation"],
    "안내": ["가이드", "도움말"],
    "등록": ["신청", "가입"],
    "알려줘": ["설명", "tell me"],
}

_PHRASE_SYNONYM_MAP: Dict[str, List[str]] = {
    "entra app": ["엔트라 앱"],
    "entra id app": ["entra app"],
    "entraapp 신청": ["entra app 신청", "엔트라앱 신청"],
}


def _ensure_config() -> None:
    missing = []
    if not AppConfig.AIS_ENDPOINT:
        missing.append("AIS_ENDPOINT")
    if not AppConfig.AIS_API_KEY:
        missing.append("AIS_API_KEY")
    if not AppConfig.AIS_INDEX:
        missing.append("AIS_INDEX")
    if not AppConfig.AOAI_ENDPOINT:
        missing.append("AOAI_ENDPOINT")
    if not AppConfig.AOAI_API_KEY:
        missing.append("AOAI_API_KEY")
    if missing:
        raise RuntimeError(f"필수 환경변수가 비어 있습니다: {', '.join(missing)}")


def _get_search_client() -> SearchClient:
    global _search_client
    if _search_client is None:
        _ensure_config()
        _search_client = SearchClient(
            endpoint=AppConfig.AIS_ENDPOINT,
            index_name=AppConfig.AIS_INDEX,
            credential=AzureKeyCredential(AppConfig.AIS_API_KEY),
        )
        logger.info("SearchClient 생성 완료: index=%s", AppConfig.AIS_INDEX)
    return _search_client


def _get_embedding_client() -> AzureOpenAI:
    global _embedding_client
    if _embedding_client is None:
        _ensure_config()
        endpoint = cast(str, AppConfig.AOAI_ENDPOINT or "").rstrip("/")
        api_key = cast(str, AppConfig.AOAI_API_KEY or "")
        _embedding_client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=AppConfig.AOAI_API_VERSION,
        )
        logger.info("AzureOpenAI 임베딩 클라이언트 생성 완료")
    return _embedding_client


def _insert_space_between_alnum_hangul(text: str) -> str:
    result = re.sub(r"([A-Za-z0-9])([가-힣])", r"\1 \2", text)
    result = re.sub(r"([가-힣])([A-Za-z0-9])", r"\1 \2", result)
    return result


def _normalize_query_text(query: str) -> tuple[str, List[str]]:
    if not query:
        return "", []
    text = query.strip()
    applied: List[str] = []
    for src, dest in _COMPOUND_REPLACEMENTS:
        if src in text:
            text = text.replace(src, dest)
            applied.append(f"{src}->{dest}")
    text = _insert_space_between_alnum_hangul(text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(), applied


def _expand_synonyms(normalized: str) -> List[str]:
    if not normalized:
        return []
    tokens = [tok for tok in re.split(r"\s+", normalized.lower()) if tok]
    expansions: Set[str] = set()
    for token in tokens:
        expansions.update(_SYNONYM_MAP.get(token, []))
    normalized_lower = normalized.lower()
    for phrase, syns in _PHRASE_SYNONYM_MAP.items():
        if phrase in normalized_lower:
            expansions.update(syns)
    expansions.discard(normalized_lower)
    return sorted({syn for syn in expansions if syn})


def _prepare_query_plan(query: str) -> Dict[str, Any]:
    normalized, applied_replacements = _normalize_query_text(query)
    expansion_terms = _expand_synonyms(normalized)
    search_terms: List[str] = []
    if normalized:
        search_terms.append(normalized)
    search_terms.extend(expansion_terms)
    search_text = " ".join(dict.fromkeys(term for term in search_terms if term)) or query
    vector_query_text = normalized or query
    plan = {
        "original_query": query,
        "normalized_query": normalized,
        "search_text": search_text,
        "vector_query_text": vector_query_text,
        "expansion_terms": expansion_terms,
        "applied_replacements": applied_replacements,
    }
    return plan


def _vectorize_query(query: str) -> List[float]:
    embedding_client = _get_embedding_client()
    response = embedding_client.embeddings.create(
        model=AppConfig.AOAI_EMBED_DEPLOYMENT,
        input=query,
    )
    vector = response.data[0].embedding
    logger.debug("임베딩 생성 길이=%d", len(vector))
    return vector


def _materialize_result(doc: Any) -> Dict[str, Any]:
    doc_dict = {key: doc.get(key) for key in doc.keys()}  # type: ignore[attr-defined]
    doc_dict["score"] = doc.get("@search.score")
    doc_dict["reranker_score"] = doc.get("@search.reranker_score")
    return doc_dict


def search_top_k(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Azure Cognitive Search에서 상위 K건을 검색한다."""
    plan = _prepare_query_plan(query)
    if not plan["vector_query_text"].strip():
        logger.warning("빈 쿼리가 전달되었습니다. 빈 결과를 반환합니다.")
        return {"docs": [], "meta": plan}

    try:
        client = _get_search_client()
        vector = _vectorize_query(plan["vector_query_text"])

        vector_query = VectorizedQuery(
            vector=vector,
            k_nearest_neighbors=top_k,
            fields="text_vector",
        )

        results = client.search(
            search_text=plan["search_text"],
            vector_queries=[vector_query],
            select=["chunk_id", "parent_id", "chunk", "title", "content"],
            top=top_k,
        )

        docs: List[Dict[str, Any]] = []
        for doc in results:
            if not doc.get("chunk"):
                logger.debug("빈 chunk 문서 스킵: id=%s", doc.get("chunk_id"))
                continue
            docs.append(_materialize_result(doc))

        plan["returned_docs"] = len(docs)
        logger.info(
            "검색 완료: raw='%s', normalized='%s', expanded=%s, 반환=%d건",
            plan["original_query"],
            plan["normalized_query"],
            plan["expansion_terms"],
            len(docs),
        )
        return {"docs": docs, "meta": plan}

    except Exception as exc:  # noqa: BLE001
        logger.error("검색 중 오류: %s", exc, exc_info=True)
        plan["error"] = str(exc)
        return {"docs": [], "meta": plan}
