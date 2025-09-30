"""
chain.py : RAG 체인 실행
- 검색 결과를 컨텍스트로 묶어 LLM에게 전달
"""

import logging
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from app.config import AppConfig
from app.rag.retriever import search_top_k

logger = logging.getLogger("entraaid_app")


def answer_with_rag(question: str, top_k: int = 3) -> dict:
    """
    검색 + LLM 조합으로 답변 생성
    """
    try:
        # 1. Azure Cognitive Search 검색 실행
        docs = search_top_k(question, top_k=top_k)

        # 2. 검색 결과를 컨텍스트로 합치기
        context_texts = [doc.get("chunk", "") for doc in docs if doc.get("chunk")]
        context = "\n\n".join(context_texts)

        logger.info("컨텍스트 구성 완료: 문서 %d개 연결", len(context_texts))

        if not context:
            logger.warning("컨텍스트 텍스트가 비어 있습니다. 빈 컨텍스트로 진행합니다.")

        # 3. 시스템 프롬프트 정의
        system_prompt = f"""
        너는 Entra ID App 관리 가이드에 대한 전문 AI 어시스턴트야.
        아래 문맥(Context)을 바탕으로 질문에 답변해.
        만약 컨텍스트에 답이 없으면 "Entra ID App 주제에 관련된 질문만 가능합니다.예) EntraApp 신청 서비스플로우에 대해서 알려줘 " 라고 답해.

        [Context]
        {context}
        """

        # 4. Azure OpenAI Chat 모델 초기화 (최신 SDK 스타일)
        llm = AzureChatOpenAI(
            azure_endpoint=AppConfig.AOAI_ENDPOINT,
            api_key=AppConfig.AOAI_API_KEY,
            api_version=AppConfig.AOAI_API_VERSION,
            model=AppConfig.AOAI_DEPLOYMENT,
        )
        logger.info("AzureChatOpenAI 초기화 성공")

        # 5. LLM 호출 (invoke 사용, __call__ deprecated 방지)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=question),
        ])
        logger.info("LLM 응답 생성 성공")

        # 6. 결과 반환 (dict 형태)
        return {
            "question": question,
            "context": context,
            "answer": response.content,
        }

    except Exception as e:
        logger.error("❌ RAG 체인 실행 중 오류 발생: %s", e, exc_info=True)
        return {
            "question": question,
            "context": "",
            "answer": f"오류가 발생했습니다: {e}",
        }
