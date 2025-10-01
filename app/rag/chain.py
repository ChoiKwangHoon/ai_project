"""
RAG 체인 구성 모듈.
검색 결과 컨텍스트를 LLM 프롬프트에 결합해 답변을 생성한다.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import SecretStr

from app.config import AppConfig
from app.rag.prompts import SYSTEM_PROMPT, build_context_block, build_user_prompt
from app.rag.retriever import search_top_k

logger = logging.getLogger("entraaid_app")


greeting_prompt = PromptTemplate(
    input_variables=["question"],
    template=(
        "당신은 Entra ID App 안내 챗봇입니다.\n"
        "사용자가 인사할 때 친근하게 환영하고 도움을 제안하세요.\n"
        "질문: {question}"
    ),
)

guide_prompt = (
    PromptTemplate(
        input_variables=["context_block", "user_prompt"],
        template=(
            "{system_prompt}\n\n"
            "{context_block}\n\n"
            "질문: {user_prompt}"
        ),
    ).partial(system_prompt=SYSTEM_PROMPT)
)

default_prompt = PromptTemplate(
    input_variables=["question"],
    template=(
        "당신은 Entra ID App 안내 챗봇입니다.\n"
        "질문이 담당 범위를 벗어나면 정중하게 Entra ID App 관련 질문을 요청하세요.\n"
        "질문: {question}"
    ),
)


llm = AzureChatOpenAI(
    azure_endpoint=AppConfig.AOAI_ENDPOINT,
    api_key=SecretStr(AppConfig.AOAI_API_KEY) if AppConfig.AOAI_API_KEY is not None else None,
    api_version=AppConfig.AOAI_API_VERSION,
    model=AppConfig.AOAI_DEPLOYMENT,
)


greeting_chain = LLMChain(llm=llm, prompt=greeting_prompt)
guide_chain = LLMChain(llm=llm, prompt=guide_prompt)
default_chain = LLMChain(llm=llm, prompt=default_prompt)


_GUIDE_KEYWORDS: List[str] = [
    "가이드",
    "entra",
    "entra id",
    "entraid",
    "entraapp",
    "ktauth",
    "설명",
    "구성",
    "설치",
]
_GREETING_KEYWORDS: List[str] = [
    "안녕",
    "hello",
    "hi",
    "hey",
    "안녕하세요",
]


def _normalize_question(question: str) -> str:
    return (question or "").strip().lower()


def route_func(question: str) -> str:
    normalized = _normalize_question(question)
    if not normalized:
        return "default"
    if any(keyword in normalized for keyword in _GREETING_KEYWORDS):
        return "greeting"
    if any(keyword in normalized for keyword in _GUIDE_KEYWORDS):
        return "guide"
    return "default"


def run_router_chain(question: str, context_text: str, preset_route: Optional[str] = None) -> Dict[str, Any]:
    route = preset_route or route_func(question)
    if route == "greeting":
        result = greeting_chain({"question": question})
    elif route == "guide":
        context_block = build_context_block(context_text)
        user_prompt = build_user_prompt(question)
        result = guide_chain({"context_block": context_block, "user_prompt": user_prompt})
    else:
        result = default_chain({"question": question})
    return {"route": route, "result": result}


def _build_context_text(docs: Sequence[Dict[str, Any]]) -> str:
    chunks = [str(doc.get("chunk", "")).strip() for doc in docs if doc.get("chunk")]
    return "\n\n".join(filter(None, chunks))


def answer_with_rag(question: str, top_k: int = 3) -> Dict[str, Any]:
    """검색과 LLM을 조합해 답변을 생성한다."""
    try:
        search_output = search_top_k(question, top_k=top_k)
        if isinstance(search_output, dict):
            docs = search_output.get("docs", [])
            search_meta = search_output.get("meta", {})
        else:
            docs = search_output  # type: ignore[assignment]
            search_meta = {}

        context_text = _build_context_text(docs)
        route = route_func(question)

        if not context_text and route == "guide":
            logger.warning("검색 결과 컨텍스트가 비어 있습니다. 빈 컨텍스트로 LLM을 호출합니다.")

        chain_output = run_router_chain(question, context_text, preset_route=route)
        result_payload: Dict[str, Any] = chain_output.get("result", {})  # type: ignore[arg-type]
        answer_text = result_payload.get("text") if isinstance(result_payload, dict) else result_payload

        response = {
            "question": question,
            "answer": answer_text,
            "route": chain_output.get("route"),
            "context": context_text if chain_output.get("route") == "guide" else "",
            "sources": docs if chain_output.get("route") == "guide" else [],
            "search_meta": search_meta,
        }

        logger.info(
            "RAG 응답 생성 완료: route=%s, 컨텍스트 문서 수=%d",
            response.get("route"),
            len(docs),
        )
        return response

    except Exception as exc:  # noqa: BLE001
        logger.error("RAG 체인 실행 중 오류 발생: %s", exc, exc_info=True)
        return {
            "question": question,
            "context": "",
            "answer": f"오류가 발생했습니다: {exc}",
            "route": "error",
            "sources": [],
            "search_meta": {},
        }
