import streamlit as st
from app.rag.chain import answer_with_rag

# ===== 페이지 설정 =====
st.set_page_config(
    page_title="Entra ID App Guide Chatbot",
    page_icon="🤖",
    layout="wide",
)

# ===== 커스텀 CSS =====
# ==== 채팅 버블 스타일 (살짝만 개선) ====
st.markdown(
    """
    <style>
    /* ===== 사이드바 버튼 스타일 수정 ===== */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #2563eb !important;  /* Azure 블루 */
        color: #ffffff !important;             /* 흰색 글씨 */
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: background-color 0.2s ease-in-out;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #1e40af !important;  /* 더 진한 파랑 */
        color: #ffffff !important;             /* 글씨는 계속 흰색 */
    }
    </style>
    """,
    unsafe_allow_html=True
)






# ===== 세션 상태 초기화 =====
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

# ===== 사이드바 =====
with st.sidebar:
    st.header("💬 대화 히스토리")

    if st.button("🆕 새 대화 시작"):
        st.session_state.qa_history = []

    for i, qa in enumerate(st.session_state.qa_history):
        question_preview = qa.get("question", "")[:20] + "..."
        answer_preview = qa.get("answer", "")[:20] + "..."
        if st.button(question_preview, key=f"q_{i}", help=answer_preview):
            st.session_state.selected_qa = qa

    st.markdown("---")
    st.caption(f"📌 Index: `{st.session_state.get('index_name','rag-khchoi')}`")
    st.caption("🔑 Model: gpt-4o-mini")
    st.caption("🌍 Env: dev")

# ===== 메인 영역 =====
st.title("🤖 Entra ID App Guide Chatbot")

if "selected_qa" in st.session_state:
    st.subheader("📌 저장된 대화")
    st.write(f"**Q:** {st.session_state.selected_qa['question']}")
    st.write(f"**A:** {st.session_state.selected_qa['answer']}")
    st.markdown("---")

# ===== 질문 입력 =====
user_input = st.chat_input("무엇이든 물어보세요!")

if user_input:
    with st.spinner("AI가 생각 중... 🤔"):
        result = answer_with_rag(user_input, top_k=3)

    # 대화 기록 저장
    st.session_state.qa_history.append(result)

    # 사용자 질문 버블
    st.markdown(f'<div class="user-bubble">{user_input}</div>', unsafe_allow_html=True)

    # AI 답변 버블
    st.markdown(f'<div class="assistant-bubble">{result["answer"]}</div>', unsafe_allow_html=True)

    # 컨텍스트 박스
    if result.get("context"):
        with st.expander("📖 참고 문서 컨텍스트"):
            st.text(result["context"])
