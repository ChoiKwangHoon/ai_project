"""
prompts.py : 프롬프트 관련 유틸리티
"""

from typing import Optional

from app.core.logger import logger


SYSTEM_PROMPT = (
    "당신은 사내 문서를 기반으로 답변하는 Entra ID App 안내 도우미입니다."
    " 다음 규칙을 반드시 지키세요:\n"
    "1) 모르는 내용은 추측하지 말고 '출처 정보가 없습니다'라고 답변합니다.\n"
    "2) 근거가 되는 출처 문서의 핵심 문장을 요약합니다.\n"
    "3) 민감한 정보는 주의 깊게 검증한 뒤 답변합니다.\n"
    "4) 답변 마지막에 참고한 문서 목록을 나열합니다."
)


def build_context_block(context_text: str) -> str:
    """검색된 컨텍스트를 모델에 전달할 블록 문자열로 변환한다."""
    if not context_text or not context_text.strip():
        logger.warning("컨텍스트 텍스트가 비어 있습니다. 빈 컨텍스트로 진행합니다.")
        return "/* 컨텍스트 없음 */"

    return f"<<CONTEXT_START>>\n{context_text}\n<<CONTEXT_END>>"


def build_user_prompt(user_question: str, extra_instruction: Optional[str] = None) -> str:
    """사용자 질문과 추가 지시를 결합해 최종 사용자 프롬프트를 만든다."""
    if not user_question or not user_question.strip():
        raise ValueError("user_question 값이 비어 있습니다.")

    question = user_question.strip()
    if extra_instruction and extra_instruction.strip():
        return f"{question}\n\n[추가 지시]\n{extra_instruction.strip()}"
    return question
