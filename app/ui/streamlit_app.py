# streamlit_app.py
import streamlit as st
from app.rag.chain import answer_with_rag
import html  # ✅ escape를 위해 추가
import re    # ✅ 하이라이트 처리를 위해 추가

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
        margin: 15px 0;  /* 말풍선 간격 늘림 */
        width: 100%;
    }

    /* ===== 사용자(User) 채팅 버블 ===== */
    .user-bubble {
        background-color: #2563eb;
        color: white;
        padding: 8px 12px;     /* 패딩 조금 줄임 */
        border-radius: 15px;
        max-width: 50%;        /* 최대 폭 줄임 */
        width: fit-content;    /* 내용에 맞는 크기 */
        margin-left: auto;     /* 오른쪽 정렬 */
        margin-bottom: 10px;   /* 아래 여백 추가 */
        text-align: right;
        word-wrap: break-word;
        display: inline-block;
    }

    /* ===== 어시스턴트(AI) 채팅 버블 ===== */
    .assistant-bubble {
        background-color: #f3f4f6;
        color: black;
        padding: 10px 14px;
        border-radius: 15px;
        max-width: 70%;
        margin-right: auto;    /* 왼쪽 정렬 */
        margin-bottom: 10px;   /* 아래 여백 추가 */
        text-align: left;
        word-wrap: break-word;
    }

    /* ===== 컨텍스트 박스 크기/스크롤 조정 ===== */
    div[data-testid="stExpander"] {
        width: 100% !important;   /* 가로 최대 100% */
        max-width: 100% !important;
    }

    /* 컨텐츠 영역: 가독성 향상 */
    pre.context-pre {
        white-space: pre-wrap;
        word-break: break-word;
        background-color: #fff8dc;   /* 연한 노랑 배경 (문맥 영역) */
        padding: 10px;
        border-radius: 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        width: 100%;
        max-width: 100%;
        max-height: 500px;          /* 세로 최대 500px */
        overflow: auto;              /* 긴 내용 스크롤 */
        box-sizing: border-box;
        tab-size: 4;                 /* 탭 너비 지정 */
        -moz-tab-size: 4;
    }

    /* 엄격 보존 모드: 줄바꿈/탭/공백을 그대로 보존하고 자동 줄바꿈을 하지 않음 */
    pre.context-pre.strict {
        white-space: pre;            /* 자동 줄바꿈 비활성화 */
        overflow: auto;
    }

    /* 질문과 관련된 텍스트 하이라이트 */
    mark.context-highlight {
        background: #ffe082;         /* 노란색 하이라이트 */
        padding: 0 2px;
        border-radius: 2px;
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
    """채팅 버블 렌더링 (개선된 스타일)"""
    cls = "user-bubble" if role == "user" else "assistant-bubble"
    with st.container():
        st.markdown(
            f'<div class="chat-container"><div class="{cls}">{content}</div></div>', 
            unsafe_allow_html=True
        )

def _extract_query_tokens(query: str | None) -> list[str]:
    """질의에서 의미있는 키워드만 추출 (한/영/숫자, 길이 2+)."""
    if not query:
        return []
    tokens = [t for t in re.split(r"\s+", query or "") if len(t) >= 2]
    tokens = [re.sub(r"[^\w가-힣]", "", t) for t in tokens]
    tokens = [t for t in tokens if t]
    # 중복 제거
    return sorted(set(tokens), key=len, reverse=True)


def _highlight_context(text: str, query: str | None, enabled: bool = True, color: str = "#ffe082") -> str:
    """컨텍스트 텍스트 내에서 질문 키워드를 노란색으로 <mark> 처리.
    - HTML 이스케이프 후, 정규식으로 안전하게 매칭
    - 너무 긴 키워드는 제외, 공백/특수문자만 있는 토큰 제외
    """
    safe = html.escape(text or "")
    if not query or not enabled:
        return safe
    tokens = _extract_query_tokens(query)
    if not tokens:
        return safe

    def repl_factory(token: str):
        return lambda m: f'<mark class="context-highlight" style="background:{color}">{m.group(0)}</mark>'

    highlighted = safe
    for tok in tokens:
        highlighted = re.sub(
            re.escape(html.escape(tok)),
            repl_factory(tok),
            highlighted,
            flags=re.IGNORECASE,
        )
    return highlighted


def _extract_snippets(text: str, query: str | None, max_snippets: int = 3, window: int = 100) -> str:
    """질문 키워드 주변만 발췌하여 스니펫 생성.
    - 각 매칭 토큰 주변으로 window 길이만큼 추출
    - 중복/겹침 영역은 병합
    """
    if not text or not query:
        return text or ""
    tokens = _extract_query_tokens(query)
    if not tokens:
        return text

    lower_text = text
    spans: list[tuple[int, int]] = []
    for tok in tokens:
        for m in re.finditer(re.escape(tok), lower_text, flags=re.IGNORECASE):
            start = max(0, m.start() - window)
            end = min(len(text), m.end() + window)
            spans.append((start, end))

    if not spans:
        return text

    # 겹치는 구간 병합
    spans.sort()
    merged = []
    cur_s, cur_e = spans[0]
    for s, e in spans[1:]:
        if s <= cur_e:
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))

    # 최대 스니펫 수 제한
    merged = merged[:max_snippets]
    parts = []
    for (s, e) in merged:
        snippet = text[s:e].strip()
        parts.append(snippet)
    sep = "\n\n…\n\n"
    return sep.join(parts)


def _compute_token_stats(text: str, query: str | None) -> tuple[int, int, float]:
    """질문 토큰 매칭 통계 (매칭 토큰 수, 전체 토큰 수, 비율[0~1])."""
    tokens = _extract_query_tokens(query)
    if not text or not tokens:
        return (0, len(tokens), 0.0)
    present = 0
    for t in tokens:
        if re.search(re.escape(t), text, flags=re.IGNORECASE):
            present += 1
    ratio = present / len(tokens) if tokens else 0.0
    return (present, len(tokens), ratio)


def _normalize_context_text(text: str) -> str:
    """컨텍스트 텍스트 정규화
    - CRLF/CR을 LF로 통일
    - 문자열에 포함된 리터럴 "\\n"/"\\t"를 실제 줄바꿈/탭으로 변환
    - 과도한 공백 라인은 최대 2줄로 제한
    """
    if not text:
        return ""
    # 줄바꿈 통일
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    # 리터럴 시퀀스 처리
    s = s.replace("\\n", "\n").replace("\\t", "\t")
    # 특수 공백을 일반 공백으로 교체 (No-Break Space 등)
    s = s.replace("\u00A0", " ")
    s = s.replace("\u2007", " ")
    s = s.replace("\u202F", " ")
    # 3줄 이상 연속 빈 줄은 2줄로 축약
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s


def render_context_box(context_text: str, query: str | None = None):
    """컨텍스트 박스
    - 가로 100%, 세로 최대 500px 스크롤
    - 하이라이트 토글, 전체/스니펫 보기
    - 관련도 표시, 다운로드 버튼
    """
    if not context_text:
        return
    # 각 컨텍스트별 위젯 키를 안정적으로 분리
    ctx_key = str(abs(hash((context_text[:50], query or ""))) % 10_000_000)
    with st.expander("📖 참고 문서 컨텍스트", expanded=False):
        c1, c2 = st.columns([3, 1])
        with c1:
            view_mode = st.radio(
                "보기 모드",
                options=["전체", "스니펫"],
                horizontal=True,
                key=f"view_{ctx_key}",
            )
            highlight_on = st.checkbox(
                "하이라이트",
                value=True,
                key=f"hl_{ctx_key}",
                help="질문과 매칭되는 텍스트를 노란색으로 강조합니다.",
            )
            # 하이라이트 색상 선택
            color_label_map = {
                "노랑": "#ffe082",
                "연파랑": "#b3e5fc",
                "연초록": "#c8e6c9",
                "연분홍": "#f8bbd0",
            }
            color_name = st.selectbox(
                "하이라이트 색상",
                options=list(color_label_map.keys()),
                index=0,
                key=f"hlcolor_{ctx_key}",
            )
            highlight_color = color_label_map[color_name]
        with c2:
            matched, total, ratio = _compute_token_stats(context_text, query)
            st.caption("관련도")
            st.progress(int(max(0, min(1, ratio)) * 100))
            st.caption(f"{matched}/{total} 키워드 매칭")

        # 표시 전 정규화 옵션
        normalize_on = st.checkbox(
            "줄바꿈/탭 정규화",
            value=True,
            key=f"norm_{ctx_key}",
            help="리터럴 \\n, \\t를 실제 줄바꿈/탭으로 변환하고 줄바꿈을 정리합니다.",
        )
        strict_preserve = st.checkbox(
            "엄격 보존 모드(자동 줄바꿈 끄기)",
            value=False,
            key=f"strict_{ctx_key}",
            help="줄바꿈/탭/공백을 그대로 보존하고 자동 줄바꿈을 끕니다. 가로 스크롤이 생길 수 있습니다.",
        )
        tabs_to_spaces = st.checkbox(
            "탭을 공백으로 변환",
            value=False,
            key=f"tabs2sp_{ctx_key}",
            help="탭 문자를 공백 4칸으로 변환합니다.",
        )

        # 스니펫 설정 (개수/범위)
        sn1, sn2 = st.columns(2)
        with sn1:
            max_snippets = st.slider(
                "스니펫 개수",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                key=f"snc_{ctx_key}",
            )
        with sn2:
            window = st.slider(
                "스니펫 범위(문자)",
                min_value=50,
                max_value=200,
                value=100,
                step=10,
                key=f"snw_{ctx_key}",
            )

        base_text = _normalize_context_text(context_text) if normalize_on else context_text
        if tabs_to_spaces and base_text:
            base_text = base_text.replace("\t", " " * 4)

        if view_mode == "스니펫":
            display_text = _extract_snippets(base_text, query, max_snippets=max_snippets, window=window)
        else:
            display_text = base_text

        highlighted_html = _highlight_context(display_text, query, enabled=highlight_on, color=highlight_color)
        pre_class = "context-pre strict" if strict_preserve else "context-pre"
        st.markdown(
            f'<pre class="{pre_class}">{highlighted_html}</pre>',
            unsafe_allow_html=True,
        )

        st.download_button(
            label="⬇ 컨텍스트 저장 (TXT)",
            data=context_text,
            file_name="context.txt",
            mime="text/plain",
            use_container_width=True,
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
            render_context_box(saved.get("context"), query=saved.get("question"))
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
        render_context_box(context_text, query=prompt)

    st.session_state.qa_history.append(
        {"question": prompt, "answer": answer, "context": context_text or None}
    )
    st.session_state.selected_qa_index = None
