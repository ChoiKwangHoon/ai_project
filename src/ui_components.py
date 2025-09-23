"""
ui_components.py
- Streamlit UI 구성 요소
"""

import streamlit as st

def chatbot_tab(qa_chain, db_manager):
    user_input = st.text_input("질문을 입력하세요:", "")
    if user_input:
        result = qa_chain({"question": user_input})
        answer = result.get("answer", result.get("result", ""))
        sources = result.get("sources", "")

        st.write("### 답변")
        st.write(answer)

        if sources:
            st.write("### 📖 참고 문서")
            for src in sources.split(","):
                st.markdown(f"- {src.strip()}")

        db_manager.insert_log(user_input, answer)

def dashboard_tab(db_manager):
    st.subheader("📌 최근 질문 로그")
    rows = db_manager.get_recent_logs(limit=10)
    for q, a in rows:
        st.markdown(f"**Q:** {q}\n\n👉 {a}\n---")

    st.subheader("🔥 Top FAQ (가장 많이 물어본 질문)")
    rows = db_manager.get_top_faq(limit=5)
    for q, cnt in rows:
        st.markdown(f"- {q} ({cnt}회)")
