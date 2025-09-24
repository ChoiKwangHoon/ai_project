"""
config.py
- 프로젝트 전역 설정 (Azure OpenAI 기준)
"""
import os
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()

# -------------------------------
# 🔹 Azure OpenAI 설정
# -------------------------------
LLM_MODEL = os.getenv("AZURE_LLM_DEPLOYMENT", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

# -------------------------------
# 🔹 PDF 문서 경로
# -------------------------------
PDF_FILE = os.path.join(os.path.dirname(__file__), "..", "entra_app_guide.pdf")

# -------------------------------
# 🔹 PostgreSQL 설정
# -------------------------------
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "entra_db")
PG_USER = os.getenv("PG_USER", "entra_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password123")
