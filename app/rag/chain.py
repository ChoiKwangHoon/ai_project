"""
chain.py : RAG 체인 실행
- 검색 결과를 컨텍스트로 묶어 LLM에게 전달
"""

# 필요한 라이브러리 임포트
import logging  # 로깅을 위한 라이브러리
from langchain.chains.router.multi_prompt_prompt import MULTI_PROMPT_ROUTER_TEMPLATE  # 다중 프롬프트 라우터 템플릿
from langchain.chains import LLMChain  # 기본 LLM 체인
from langchain.prompts import PromptTemplate  # 프롬프트 템플릿
from langchain_openai import AzureChatOpenAI  # Azure OpenAI 서비스
from pydantic import SecretStr  # 보안 문자열 처리
from app.config import AppConfig  # 앱 설정
from app.rag.retriever import search_top_k  # 검색 기능

logger = logging.getLogger("entraaid_app")


# 1. 각 주제별 프롬프트/체인 정의
greeting_prompt = PromptTemplate.from_template(
"""
너는 Entra ID App 관리 가이드 전문 AI 어시스턴트야.
인사에는 '안녕하세요! Entra ID App 관련하여 어떤 것을 도와드릴까요?'라고 답해.
"""
)
guide_prompt = PromptTemplate.from_template(
    "너는 Entra ID App 관리 가이드 전문 AI야. 아래 문맥을 참고해 답변해.\n[Context]\n{context}\n질문: {question}"
)
default_prompt = PromptTemplate.from_template(
    "죄송합니다. Entra ID App과 관련된 질문만 답변할 수 있습니다. 다른 질문이 있다면 말씀해 주세요."
)
llm = AzureChatOpenAI(
    azure_endpoint=AppConfig.AOAI_ENDPOINT,
    api_key=SecretStr(AppConfig.AOAI_API_KEY) if AppConfig.AOAI_API_KEY is not None else None,
    api_version=AppConfig.AOAI_API_VERSION,
    model=AppConfig.AOAI_DEPLOYMENT,
)


# 각 용도별 체인 생성
greeting_chain = LLMChain(llm=llm, prompt=greeting_prompt)  # 인사 응답용 체인
guide_chain = LLMChain(llm=llm, prompt=guide_prompt)       # Entra ID 가이드 응답용 체인
default_chain = LLMChain(llm=llm, prompt=default_prompt)   # 기본 응답용 체인

# 2. Router 분기 조건 함수
def route_func(inputs):
    question = inputs["question"].lower()
    if "안녕" in question or "hello" in question or "hi" in question:  # "hi" 추가
        return "greeting"
    elif any(keyword in question for keyword in ["앱", "가이드", "entra", "entraApp", "KTAUTH"]):
        return "guide"
    else:
        return "default"

# 3. 라우팅 체인 직접 구현
def run_router_chain(question, context):
    route = route_func({"question": question})
    if route == "greeting":
        return greeting_chain({"question": question})
    elif route == "guide":
        return guide_chain({"question": question, "context": context})
    else:
        return default_chain({"question": question})

# 4. answer_with_rag 함수에서 RouterChain 사용
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

        # 3. 라우팅 체인 직접 실행하여 답변 생성
        route = route_func({"question": question})  # 라우팅 경로 먼저 확인
        result = run_router_chain(question, context)
        logger.info("LLM 응답 생성 성공")

        # 4. 결과 반환 (dict 형태)
        return {
            "question": question,
            "context": context if route == "guide" else "",  # guide 경로일 때만 컨텍스트 포함
            "answer": result["text"] if "text" in result else result,
            "route": route  # 라우팅 경로 정보 추가
        }

    except Exception as e:
        logger.error("❌ RAG 체인 실행 중 오류 발생: %s", e, exc_info=True)
        return {
            "question": question,
            "context": "",
            "answer": f"오류가 발생했습니다: {e}",
        }
