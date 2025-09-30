# 타입 힌트에서 List 사용
from typing import List

# 공용 로거 불러오기
from app.core.logger import logger


def chunk_text(texts: List[str], chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    텍스트 리스트를 일정한 크기로 분할하는 함수
    (방어 로직 + 로그 기록 포함)
    :param texts: 여러 페이지에서 추출된 텍스트 리스트
    :param chunk_size: 분할할 최대 단어 수 (기본값 500)
    :param overlap: 청킹 시 중복 단어 수 (기본값 50)
    :return: 분할된 텍스트 덩어리 리스트
    """

    # 입력값 방어 로직: None 또는 빈 리스트인 경우
    if not texts:
        logger.warning("청킹할 텍스트가 비어 있습니다. 빈 리스트 반환.")
        return []

    # 파라미터 검증: overlap이 chunk_size보다 크면 비정상
    if overlap >= chunk_size:
        logger.error(f"잘못된 파라미터: overlap({overlap}) >= chunk_size({chunk_size})")
        raise ValueError("overlap은 chunk_size보다 작아야 합니다.")

    # 최종 결과를 담을 리스트
    chunks = []

    # 입력된 텍스트 리스트 순회
    for idx, text in enumerate(texts):
        if not text or not text.strip():
            logger.warning(f"{idx}번째 텍스트가 비어 있어 건너뜀")
            continue

        # 단어 단위로 분리
        words = text.split()
        start = 0

        # 텍스트 끝까지 순회하며 청킹 진행
        while start < len(words):
            end = min(start + chunk_size, len(words))
            # 단어들을 다시 하나의 문자열로 합치기
            chunk = " ".join(words[start:end])

            # 빈 문자열 방어
            if chunk.strip():
                chunks.append(chunk)
                logger.debug(
                    f"{idx}번째 텍스트에서 청크 생성 "
                    f"(단어 {start}~{end}, 길이 {len(chunk)}자)"
                )
            else:
                logger.warning(f"{idx}번째 텍스트에서 빈 청크 생성됨 (무시)")

            # overlap 만큼 겹치도록 시작점 이동
            start += chunk_size - overlap

    # 결과 요약 로그
    logger.info(f"청킹 완료: 총 {len(chunks)}개 청크 생성")

    return chunks
