# pathlib에서 Path 클래스를 불러오기 (파일 경로 다루기 위함)
from pathlib import Path

# 타입 힌트를 위해 List 불러오기
from typing import List

# pypdf 라이브러리에서 PDF 읽기 기능을 제공하는 PdfReader 불러오기
from pypdf import PdfReader

# 공용 로거 불러오기
from app.core.logger import logger


def load_pdf(file_path: str) -> List[str]:
    """
    PDF 파일에서 텍스트를 추출하는 함수 (방어 로직 + 로그 포함)
    :param file_path: 로컬 PDF 파일 경로
    :return: 각 페이지별 텍스트를 담은 리스트
    """

    # 파일 경로 객체 생성
    path = Path(file_path)

    # 파일이 존재하지 않으면 에러 발생 + 로그 기록
    if not path.exists():
        logger.error(f"PDF 파일을 찾을 수 없습니다: {file_path}")
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {file_path}")

    # PDF 파일 열기 (에러 방어)
    try:
        reader = PdfReader(str(path))
        logger.info(f"PDF 파일 열기 성공: {file_path}, 총 {len(reader.pages)} 페이지")
    except Exception as e:
        logger.exception(f"PDF 파일을 열 수 없습니다: {file_path}")
        raise RuntimeError(f"PDF 파일을 열 수 없습니다: {file_path}, 에러: {e}")

    # 추출된 텍스트를 담을 리스트
    texts = []

    # 페이지 단위로 텍스트 추출
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text and text.strip():
                texts.append(text)
                logger.debug(f"{i} 페이지 텍스트 추출 성공 (길이: {len(text)}자)")
            else:
                logger.warning(f"{i} 페이지 텍스트가 비어 있음")
        except Exception as e:
            logger.exception(f"{i} 페이지 텍스트 추출 실패")
            continue  # 다음 페이지 계속 진행

    # 결과 로그 기록
    logger.info(f"PDF 텍스트 추출 완료: 총 {len(texts)} 페이지 성공")

    return texts
