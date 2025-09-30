# typing 모듈에서 Optional 불러오기 (타입 힌트용)
from typing import Optional

# 공용 로거(logger) 불러오기
from app.core.logger import logger


# 시스템 프롬프트 템플릿 (모델에게 기본 규칙을 전달)
SYSTEM_PROMPT = (
    "당신은 사내 문서 기반의 도우미입니다. 다음 규칙을 철저히 따르세요:\n"
    "1) 모르는 내용은 추측하지 말고 '출처에 정보가 없습니다'라고 답하세요.\n"
    "2) 항상 출처 문서의 핵심 문장을 근거로 요약하세요.\n"
    "3) 숫자/정책/보안 정보는 보수적으로 검증하여 답하세요.\n"
    "4) 답변 마지막에 참고한 문서의 제목과 링크를 나열하세요.\n"
)


def build_context_block(context_text: str) -> str:
    """
    검색된 컨텍스트를 모델에 전달하기 위한 블록 문자열 생성
    :param context_text: 여러 문서를 하나로 합친 컨텍스트 텍스트
    :return: 포맷팅된 컨텍스트 블록 문자열
    """
    # 방어: 컨텍스트가 비어 있으면 경고 로그
    if not context_text or not context_text.strip():
        logger.warning("컨텍스트 텍스트가 비어 있습니다. 빈 컨텍스트로 진행합니다.")
        return "/* 컨텍스트 없음 */"
    # 컨텍스트 블록을 깔끔한 구분선과 함께 제공
    return f"<<CONTEXT_START>>\n{context_text}\n<<CONTEXT_END>>"


def build_user_prompt(user_question: str, extra_instruction: Optional[str] = None) -> str:
    """
    유저 프롬프트(질문)에 선택적 추가 지시를 붙여 최종 유저 메시지를 구성
    :param user_question: 최종 사용자 질문
    :param extra_instruction: 추가 지시(선택)
    :return: 최종 유저 프롬프트
    """
    # 방어: 질문이 비어 있으면 에러
    if not user_question or not user_question.strip():
        raise ValueError("user_question 은 비어 있을 수 없습니다.")

    # 추가 지시가 있으면 덧붙이고 없으면 질문만 사용
    if extra_instruction and extra_instruction.strip():
        return f"{user_question}\n\n[추가지시]\n{extra_instruction.strip()}"
    else:
        return user_question
