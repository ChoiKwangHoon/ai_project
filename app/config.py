"""
앱 전역 환경설정 로더
- .env 파일의 값을 불러와 AppConfig 클래스에 매핑
- 필수 값이 누락된 경우 예외 발생
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class AppConfig:
    """
    애플리케이션 전역 환경설정
    """

    # ===== 앱 기본 설정 =====
    ENV: str = os.getenv("ENV", "dev")  # 실행 환경 (dev/prod)
    APP_NAME: str = os.getenv("APP_NAME", "entraid-app-guide")  # 앱 이름

    # ===== Observability =====
    OBS_MODE: str = os.getenv("OBS_MODE", "none")  # 관측 모드 (none | smith | fuse | both)

    # ===== Azure OpenAI =====
    AOAI_ENDPOINT  = os.getenv("AOAI_ENDPOINT")  # OpenAI 엔드포인트
    AOAI_DEPLOYMENT  = os.getenv("AOAI_DEPLOYMENT")  # GPT 모델 배포명
    AOAI_API_KEY  = os.getenv("AOAI_API_KEY")  # OpenAI API Key
    AOAI_EMBED_DEPLOYMENT  = os.getenv("AOAI_EMBED_DEPLOYMENT", "text-embedding-3-small")  
    # 기본값: text-embedding-3-small
    AOAI_API_VERSION  = os.getenv("AOAI_API_VERSION", "2024-12-01-preview")  
    # 기본값 최신 Preview 버전

    # ===== Azure AI Search =====
    AIS_ENDPOINT  = os.getenv("AIS_ENDPOINT", "")  # Search 엔드포인트
    AIS_API_KEY  = os.getenv("AIS_API_KEY", "")    # Search API Key
    AIS_INDEX  = os.getenv("AIS_INDEX", "entraid-app-guide-index")  # 기본 인덱스명
    AIS_INDEXER_NAME  = os.getenv("AIS_INDEXER_NAME", "entraid-app-guide-indexer")  
    # 인덱서 이름 (추가됨)

    # ===== Azure Key Vault (옵션) =====
    KEYVAULT_URL  = os.getenv("KEYVAULT_URL", "")

    # ===== Python Path =====
    PYTHONPATH  = os.getenv("PYTHONPATH", "")

    # ===== Blob Storage (옵션) =====
    BLOB_CONN_STR  = os.getenv("BLOB_CONN_STR", "")  # Blob 연결 문자열
    BLOB_CONTAINER  = os.getenv("BLOB_CONTAINER", "")  # Blob 컨테이너명

    @classmethod
    def validate(cls):
        """
        필수 환경변수가 설정되었는지 검증
        """
        missing = []
        if not cls.AOAI_ENDPOINT:
            missing.append("AOAI_ENDPOINT")
        if not cls.AOAI_DEPLOYMENT:
            missing.append("AOAI_DEPLOYMENT")
        if not cls.AOAI_API_KEY:
            missing.append("AOAI_API_KEY")
        if not cls.AIS_ENDPOINT:
            missing.append("AIS_ENDPOINT")
        if not cls.AIS_API_KEY:
            missing.append("AIS_API_KEY")

        if missing:
            raise ValueError(f"❌ 필수 환경변수가 누락되었습니다: {', '.join(missing)}")


# 실행 시점에 필수 환경변수 검증
try:
    AppConfig.validate()
except Exception as e:
    raise RuntimeError(f"환경설정 오류: {e}")
