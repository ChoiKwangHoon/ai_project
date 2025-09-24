"""
app.py
- Streamlit 메인 실행 파일
"""
from src.data_loader import load_and_split_pdf
from src.vector_store import build_vector_store
from src.rag_chain import create_rag_chain_with_sources
from src.db_manager import DBManager
from src.ui_components import chatbot_tab, dashboard_tab
from src.config import (
    PDF_FILE, LLM_MODEL, EMBEDDING_MODEL,
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
)



# 데이터 로드 & 벡터DB 생성
docs = load_and_split_pdf(PDF_FILE)
db = build_vector_store(docs, EMBEDDING_MODEL)
qa_chain = create_rag_chain_with_sources(LLM_MODEL, db)

# PostgreSQL DB 연결
db_manager = DBManager(PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD)

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🔹 Entra App 가이드 챗봇 & FAQ 대시보드")

tab1, tab2 = st.tabs(["💬 챗봇", "📊 FAQ 대시보드"])

with tab1:
    chatbot_tab(qa_chain, db_manager)

with tab2:
    dashboard_tab(db_manager)
