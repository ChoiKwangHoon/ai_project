"""
config.py
- 전역 설정값 정의
"""

import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# 모델 설정
LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# PDF 문서 경로
PDF_FILE = "entra_app_guide.pdf"

# PostgreSQL 설정
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "entra_db")
PG_USER = os.getenv("PG_USER", "entra_user")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password123")
