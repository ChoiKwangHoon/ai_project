# streamlit_app.py
import streamlit as st
from app.rag.chain import answer_with_rag
import html  # ✅ escape를 위해 추가

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
    /* ===== 채팅 컨테이너 (flexbox) ===== */
    .chat-container {
        display: flex;
        margin: 8px 0;
        width: 100%;
    }

    /* ===== 사용자(User) 채팅 버블 ===== */
    .user-bubble {
        background-color: #2563eb;
        color: white;
        padding: 10px 14px;
        border-radius: 15px;
        max-width: 70%;
        margin-left: auto;     /* 오른쪽 정렬 */
        text-align: right;
    }

    /* ===== 어시스턴트(AI) 채팅 버블 ===== */
    .assistant-bubble {
        background-color: #f3f4f6;
        color: black;
        padding: 10px 14px;
        border-radius: 15px;
        max-width: 70%;
        margin-right: auto;    /* 왼쪽 정렬 */
        text-align: left;
    }

    /* ===== 컨텍스트 박스 폭 조정 ===== */
    div[data-testid="stExpander"] {
        max-width: 600px !important;
    }

    pre.context-pre {
        white-space: pre-wrap;
        word-break: break-word;
        background-color: #fff8dc;
        padding: 8px;
        border-radius: 8px;
        font-family: monospace;
    }

    /* ===== 사이드바 버튼 스타일 (Azure 블루) ===== */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        transition: background-color 0.2s ease-in-out;
    }
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #1e40af !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ===== 기본 세션 상태 초기화 =====
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []
if "selected_qa_index" not in st.session_state:
    st.session_state.selected_qa_index = None
if "index_name" not in st.session_state:
    st.session_state.index_name = "rag-khchoi"
if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-4o-mini"
if "env_name" not in st.session_state:
    st.session_state.env_name = "dev"

# ===== 공통 함수 =====
def render_bubble(role: str, content: str):
    cls = "user-bubble" if role == "user" else "assistant-bubble"
    with st.container():
        st.markdown(f'<div class="{cls}">{content}</div>', unsafe_allow_html=True)

def render_context_box(context_text: str):
    """컨텍스트 박스 (접이식, 고정폭 500px, 고정폭 글꼴, 노란색 계열 텍스트)"""
    if not context_text:
        return
    with st.expander("📖 참고 문서 컨텍스트", expanded=False):
        safe_text = html.escape(context_text)  # ✅ 변경: escape_markdown 대신 html.escape
        st.markdown(
            f'<pre class="context-pre">{safe_text}</pre>',
            unsafe_allow_html=True,
        )

def reset_conversation():
    st.session_state.qa_history = []
    st.session_state.selected_qa_index = None


# ===== 사이드바 =====
with st.sidebar:
    st.header("💬 대화 히스토리")

    if st.button("🆕 새 대화 시작", use_container_width=True):
        reset_conversation()

    if st.session_state.qa_history:
        for i, qa in enumerate(st.session_state.qa_history):
            q = (qa.get("question") or "").strip()
            a = (qa.get("answer") or "").strip()
            q_preview = (q[:20] + "…") if len(q) > 20 else q
            a_preview = (a[:20] + "…") if len(a) > 20 else a
            if st.button(f"• {q_preview}", key=f"hist_{i}", help=a_preview, use_container_width=True):
                st.session_state.selected_qa_index = i
    else:
        st.caption("아직 저장된 대화가 없습니다.")

    st.markdown("---")
    st.caption(f"📌 Index: `{st.session_state.get('index_name')}`")
    st.caption(f"🔑 Model: {st.session_state.get('model_name')}")
    st.caption(f"🌍 Env: {st.session_state.get('env_name')}")

# ===== 메인 영역 =====
st.title("🤖 Entra ID App Guide Chatbot")

if isinstance(st.session_state.selected_qa_index, int):
    idx = st.session_state.selected_qa_index
    if 0 <= idx < len(st.session_state.qa_history):
        saved = st.session_state.qa_history[idx]
        st.subheader("📌 저장된 대화")
        render_bubble("user", saved.get("question", ""))
        render_bubble("assistant", saved.get("answer", ""))
        if saved.get("context"):
            render_context_box(saved.get("context"))
        st.markdown("---")

prompt = st.chat_input("질문을 입력하세요…")

if prompt:
    render_bubble("user", prompt)

    with st.spinner("AI가 생각 중... 🤔"):
        result = answer_with_rag(prompt, top_k=3) or {}
        answer = (result.get("answer") or "").strip()
        context_text = (result.get("context") or "").strip()

    render_bubble("assistant", answer if answer else "죄송해요, 응답을 생성하지 못했어요.")

    if context_text:
        render_context_box(context_text)

    st.session_state.qa_history.append(
        {"question": prompt, "answer": answer, "context": context_text or None}
    )
    st.session_state.selected_qa_index = None
