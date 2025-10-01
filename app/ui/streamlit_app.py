from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Optional

import streamlit as st

from app.rag.chain import answer_with_rag


# ===== 페이지 설정 =====
st.set_page_config(
    page_title="Entra ID App Guide Chatbot",
    page_icon="🧭",
    layout="wide",
)


# ===== 커스텀 CSS =====
st.markdown(
    """
    <style>
    .chat-container {
        display: flex;
        margin: 15px 0;
        width: 100%;
    }

    .user-bubble {
        background-color: #2563eb;
        color: white;
        padding: 8px 12px;
        border-radius: 15px;
        max-width: 50%;
        width: fit-content;
        margin-left: auto;
        margin-bottom: 10px;
        text-align: right;
        word-wrap: break-word;
        display: inline-block;
    }

    .assistant-bubble {
        background-color: #f3f4f6;
        color: black;
        padding: 10px 14px;
        border-radius: 15px;
        max-width: 70%;
        margin-right: auto;
        margin-bottom: 10px;
        text-align: left;
        word-wrap: break-word;
    }

    div[data-testid="stExpander"] {
        width: 100% !important;
        max-width: 100% !important;
    }

    pre.context-pre {
        white-space: pre-wrap;
        word-break: break-word;
        background-color: #fff8dc;
        padding: 10px;
        border-radius: 8px;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
                     "Liberation Mono", "Courier New", monospace;
        width: 100%;
        max-width: 100%;
        max-height: 500px;
        overflow: auto;
        box-sizing: border-box;
        tab-size: 4;
        -moz-tab-size: 4;
    }

    pre.context-pre.strict {
        white-space: pre;
        overflow: auto;
    }

    mark.context-highlight {
        background: #ffe082;
        padding: 0 2px;
        border-radius: 2px;
    }

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


# ===== 세션 상태 초기화 =====
def _init_session_state() -> None:
    defaults = {
        "qa_history": [],
        "selected_qa_index": None,
        "index_name": "rag-khchoi",
        "model_name": "gpt-4o-mini",
        "env_name": "dev",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


_init_session_state()


# ===== 공통 함수 =====
def render_bubble(role: str, content: str) -> None:
    """채팅 말풍선을 렌더링한다."""
    cls = "user-bubble" if role == "user" else "assistant-bubble"
    with st.container():
        st.markdown(
            f'<div class="chat-container"><div class="{cls}">{content}</div></div>',
            unsafe_allow_html=True,
        )


def _extract_query_tokens(query: Optional[str]) -> List[str]:
    """질문에서 길이 2 이상 키워드를 추출한다."""
    if not query:
        return []
    tokens = [t for t in re.split(r"\s+", query) if len(t) >= 2]
    tokens = [re.sub(r"[^\w가-힣]", "", t) for t in tokens]
    tokens = [t for t in tokens if t]
    return sorted(set(tokens), key=len, reverse=True)


def _highlight_context(text: str, query: Optional[str], *, enabled: bool = True, color: str = "#ffe082") -> str:
    """컨텍스트 내 검색어를 하이라이트한다."""
    safe = html.escape(text or "")
    if not query or not enabled:
        return safe

    tokens = _extract_query_tokens(query)
    if not tokens:
        return safe

    highlighted = safe
    for token in tokens:
        highlighted = re.sub(
            re.escape(html.escape(token)),
            lambda match: f'<mark class="context-highlight" style="background:{color}">{match.group(0)}</mark>',
            highlighted,
            flags=re.IGNORECASE,
        )
    return highlighted


def _extract_snippets(text: str, query: Optional[str], *, max_snippets: int = 3, window: int = 100) -> str:
    """질문 키워드 주변 발췌 구간을 추출한다."""
    if not text or not query:
        return text or ""

    tokens = _extract_query_tokens(query)
    if not tokens:
        return text

    spans: List[tuple[int, int]] = []
    for token in tokens:
        for match in re.finditer(re.escape(token), text, flags=re.IGNORECASE):
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            spans.append((start, end))

    if not spans:
        return text

    spans.sort()
    merged: List[tuple[int, int]] = []
    cur_start, cur_end = spans[0]
    for start, end in spans[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end))

    merged = merged[:max_snippets]
    snippets = [text[s:e].strip() for s, e in merged]
    return "\n\n…\n\n".join(snippets)


def _compute_token_stats(text: str, query: Optional[str]) -> tuple[int, int, float]:
    tokens = _extract_query_tokens(query)
    if not text or not tokens:
        return 0, len(tokens), 0.0
    present = sum(1 for token in tokens if re.search(re.escape(token), text, flags=re.IGNORECASE))
    ratio = present / len(tokens) if tokens else 0.0
    return present, len(tokens), ratio


def _normalize_context_text(text: str) -> str:
    """컨텍스트 텍스트를 정규화하고 가독성을 높이기 위해 줄바꿈을 보정한다."""
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\\n", "\n").replace("\\t", "\t")
    normalized = normalized.replace("\u00A0", " ").replace("\u2007", " ").replace("\u202F", " ")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r" {2,}", " ", normalized)
    normalized = re.sub(r"(?<=\S)([•\-\u2022\u2023\u25CF\u25CB])\s*", lambda m: "\n" + m.group(1) + " ", normalized)
    normalized = re.sub(r"(?<=\S)(\d+\.)\s*", lambda m: "\n" + m.group(1) + " ", normalized)
    normalized = re.sub(r"(?<=\S)(\[[^\]]+\])", lambda m: "\n" + m.group(1), normalized)
    normalized = re.sub(r"(?<=\S)(FAQ)", lambda m: "\n" + m.group(1), normalized)
    normalized = re.sub(r"(?<=\S)(수 신 자)", lambda m: "\n" + m.group(1), normalized)
    normalized = re.sub(r"(?<=\S)(메일 문의 양식)", lambda m: "\n" + m.group(1), normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _format_source_label(source: Dict[str, Any]) -> str:
    title = source.get("title") or source.get("parent_id") or source.get("chunk_id") or "출처 미상"
    score = source.get("score")
    rerank = source.get("reranker_score")

    meta_parts = []
    if isinstance(score, (int, float)):
        meta_parts.append(f"score={score:.3f}")
    if isinstance(rerank, (int, float)):
        meta_parts.append(f"rerank={rerank:.3f}")

    meta = " | ".join(meta_parts)
    if meta:
        return f"• **{title}** ({meta})"
    return f"• **{title}**"


def _summarize_search_meta(meta: Dict[str, Any]) -> List[str]:
    summary: List[str] = []
    original = meta.get("original_query")
    normalized = meta.get("normalized_query")
    if normalized and normalized != original:
        summary.append(f"정규화='{normalized}'")
    replacements = meta.get("applied_replacements") or []
    if replacements:
        summary.append("치환=" + ", ".join(map(str, replacements)))
    expansions = meta.get("expansion_terms") or []
    if expansions:
        summary.append("동의어=" + ", ".join(map(str, expansions)))
    returned = meta.get("returned_docs")
    if isinstance(returned, int):
        summary.append(f"반환 {returned}건")
    error = meta.get("error")
    if error:
        summary.append(f"오류={error}")
    return summary


def _render_search_meta(meta: Optional[Dict[str, Any]]) -> None:
    if not meta:
        return
    summary = _summarize_search_meta(meta)
    if summary:
        st.caption("🔍 검색 요약: " + " | ".join(summary))
    with st.expander("🔍 검색 상세 정보", expanded=False):
        st.write("**정규화 질의**:", meta.get("normalized_query") or "-")
        st.write("**검색 텍스트**:", meta.get("search_text") or "-")
        expansions = meta.get("expansion_terms") or []
        st.write("**동의어 확장**:", ", ".join(map(str, expansions)) or "-")
        replacements = meta.get("applied_replacements") or []
        st.write("**적용 치환 규칙**:", ", ".join(map(str, replacements)) or "-")
        returned = meta.get("returned_docs")
        st.write("**반환 문서 수**:", returned if returned is not None else "-")
        if meta.get("error"):
            st.error(str(meta["error"]))
        st.json(meta)


def render_context_box(
    context_text: str,
    *,
    query: Optional[str] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    """검색 컨텍스트를 표시한다."""
    if not context_text:
        st.info("표시할 컨텍스트가 없습니다.")
        return

    ctx_key = str(abs(hash((context_text[:50], query or "", repr(meta)))) % 10_000_000)
    with st.expander("📚 참고 문서 컨텍스트", expanded=False):
        if meta:
            summary = _summarize_search_meta(meta)
            if summary:
                st.caption("🔎 검색 메타: " + " | ".join(summary))
        col_left, col_right = st.columns([3, 1])
        with col_left:
            view_mode = st.radio(
                "보기 모드",
                options=["전체", "발췌"],
                horizontal=True,
                key=f"view_{ctx_key}",
            )
            highlight_on = st.checkbox(
                "질문 키워드 하이라이트",
                value=True,
                key=f"hl_{ctx_key}",
                help="질문과 일치하는 구간을 강조합니다.",
            )
            color_label_map = {
                "노랑": "#ffe082",
                "하늘": "#b3e5fc",
                "연두": "#c8e6c9",
                "분홍": "#f8bbd0",
            }
            color_name = st.selectbox(
                "하이라이트 색상",
                options=list(color_label_map.keys()),
                index=0,
                key=f"hlcolor_{ctx_key}",
            )
            highlight_color = color_label_map[color_name]
        with col_right:
            matched, total, ratio = _compute_token_stats(context_text, query)
            st.caption("질문과의 관련도")
            st.progress(min(max(ratio, 0.0), 1.0))
            st.caption(f"{matched}/{total} 키워드 일치")

        normalize_on = st.checkbox(
            "줄바꿈/공백 정규화",
            value=True,
            key=f"norm_{ctx_key}",
            help="리터럴 \\n, \\t 등을 실제 줄바꿈과 탭으로 변환합니다.",
        )
        strict_preserve = st.checkbox(
            "공백 보존 모드",
            value=False,
            key=f"strict_{ctx_key}",
            help="자동 줄바꿈 없이 원본 공백을 그대로 보여줍니다.",
        )
        tabs_to_spaces = st.checkbox(
            "탭을 공백 4칸으로 치환",
            value=False,
            key=f"tabs2sp_{ctx_key}",
        )

        col_snip1, col_snip2 = st.columns(2)
        with col_snip1:
            max_snippets = st.slider(
                "발췌 개수",
                min_value=1,
                max_value=5,
                value=3,
                step=1,
                key=f"snc_{ctx_key}",
            )
        with col_snip2:
            window = st.slider(
                "발췌 범위(문자)",
                min_value=50,
                max_value=200,
                value=100,
                step=10,
                key=f"snw_{ctx_key}",
            )

        base_text = _normalize_context_text(context_text) if normalize_on else context_text
        if tabs_to_spaces and base_text:
            base_text = base_text.replace("\t", " " * 4)

        if view_mode == "발췌":
            display_text = _extract_snippets(base_text, query, max_snippets=max_snippets, window=window)
        else:
            display_text = base_text

        highlighted_html = _highlight_context(display_text, query, enabled=highlight_on, color=highlight_color)
        pre_class = "context-pre strict" if strict_preserve else "context-pre"
        st.markdown(
            f'<pre class="{pre_class}">{highlighted_html}</pre>',
            unsafe_allow_html=True,
        )

        if sources:
            st.caption("참고 문서")
            for source in sources:
                st.markdown(_format_source_label(source))

        st.download_button(
            label="컨텍스트 원문 다운로드 (TXT)",
            data=context_text,
            file_name="context.txt",
            mime="text/plain",
            use_container_width=True,
        )


def reset_conversation() -> None:
    st.session_state.qa_history = []
    st.session_state.selected_qa_index = None


# ===== 사이드바 =====
with st.sidebar:
    st.header("대화 히스토리")

    if st.button("새 대화 시작", use_container_width=True):
        reset_conversation()

    if st.session_state.qa_history:
        for i, qa in enumerate(st.session_state.qa_history):
            question = (qa.get("question") or "").strip()
            answer = (qa.get("answer") or "").strip()
            q_preview = question[:20] + ("…" if len(question) > 20 else "")
            a_preview = answer[:20] + ("…" if len(answer) > 20 else "")
            if st.button(
                f"📌 {q_preview}",
                key=f"hist_{i}",
                help=a_preview or "답변 없음",
                use_container_width=True,
            ):
                st.session_state.selected_qa_index = i
    else:
        st.caption("아직 기록된 대화가 없습니다.")

    st.markdown("---")
    st.caption(f"Index: `{st.session_state.get('index_name')}`")
    st.caption(f"Model: {st.session_state.get('model_name')}")
    st.caption(f"Env: {st.session_state.get('env_name')}")


# ===== 메인 영역 =====
st.title("🔎 Entra ID App Guide Chatbot")

if isinstance(st.session_state.selected_qa_index, int):
    idx = st.session_state.selected_qa_index
    if 0 <= idx < len(st.session_state.qa_history):
        saved = st.session_state.qa_history[idx]
        st.subheader("저장된 대화")
        render_bubble("user", saved.get("question", ""))
        render_bubble("assistant", saved.get("answer", ""))
        _render_search_meta(saved.get("search_meta") or {})
        if saved.get("context"):
            render_context_box(
                saved.get("context", ""),
                query=saved.get("question"),
                sources=saved.get("sources"),
                meta=saved.get("search_meta"),
            )
        st.markdown("---")

prompt = st.chat_input("궁금한 내용을 입력하세요")

if prompt:
    render_bubble("user", prompt)

    with st.spinner("AI가 답변을 준비하고 있습니다..."):
        result = answer_with_rag(prompt, top_k=3) or {}
        answer = (result.get("answer") or "").strip()
        context_text = (result.get("context") or "").strip()
        sources = result.get("sources") or []
        route = result.get("route")
        search_meta = result.get("search_meta") or {}

    if answer:
        render_bubble("assistant", answer)
    else:
        render_bubble("assistant", "죄송합니다. 답변을 생성하지 못했습니다.")

    _render_search_meta(search_meta)

    if route != "guide" and not context_text:
        st.info("Entra ID App 관련 질문이 아니라서 일반 안내 답변을 제공했습니다.")

    if context_text:
        render_context_box(context_text, query=prompt, sources=sources, meta=search_meta)
    else:
        st.caption("참고 컨텍스트가 없어 LLM이 자체적으로 답변했습니다.")

    st.session_state.qa_history.append(
        {
            "question": prompt,
            "answer": answer,
            "context": context_text or None,
            "sources": sources,
            "search_meta": search_meta or {},
        }
    )
    st.session_state.selected_qa_index = None
