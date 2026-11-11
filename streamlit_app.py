"""실습 5: 공통 프레임과 st.navigation 진입 파일."""

import uuid

import streamlit as st
from openai import OpenAI

from config import IMAGE_MODEL, TEXT_MODEL

st.set_page_config(page_title="생성 AI 실습 · Streamlit", page_icon="📚", layout="centered")
st.session_state.setdefault("cache_session_id", uuid.uuid4().hex)


def forget_key():
    client = st.session_state.pop("openai_client", None)
    if client:
        client.close()
    for name in list(st.session_state):
        if name.startswith(("home_", "chat_messages", "library_messages", "pdf_messages")):
            st.session_state.pop(name, None)
    st.session_state.pop("key_input", None)
    st.session_state["cache_session_id"] = uuid.uuid4().hex


with st.sidebar:
    st.title("📚 생성 AI 실습")
    st.caption("텍스트 · 이미지 · 대화 · PDF 검색")
    # PDF 리소스가 있는 동안 키를 바꾸면 삭제할 수 없으므로 먼저 Leave를 사용합니다.
    pdf_active = bool(st.session_state.get("pdf_resource"))
    with st.form("api_key_form"):
        api_key = st.text_input("OpenAI API Key", type="password", key="key_input",
                                disabled=pdf_active)
        apply_key = st.form_submit_button("적용", disabled=pdf_active)
    if apply_key:
        key = api_key.strip()
        if not key:
            st.warning("API Key를 입력해 주세요.")
        else:
            old_client = st.session_state.get("openai_client")
            if old_client is None or old_client.api_key != key:
                if old_client:
                    old_client.close()
                st.session_state["openai_client"] = OpenAI(api_key=key, timeout=120.0, max_retries=0)
                st.session_state["cache_session_id"] = uuid.uuid4().hex
                for name in ("chat_messages", "library_messages", "pdf_messages"):
                    st.session_state[name] = []
                for name in ("home_result", "home_image"):
                    st.session_state.pop(name, None)
            st.success("키를 적용했습니다. 요청 시 인증됩니다.")
    if st.session_state.get("openai_client"):
        st.caption("키가 현재 세션에 설정되어 있습니다.")
        st.button("키와 대화 지우기", on_click=forget_key, disabled=pdf_active)
    if pdf_active:
        st.caption("키 변경/삭제 전 ChatPDF 페이지에서 Leave를 눌러 주세요.")
    st.divider()
    st.caption(f"텍스트: {TEXT_MODEL}\n\n이미지: {IMAGE_MODEL}")
    st.caption("키는 코드나 저장소에 저장하지 않습니다. 질문·이미지 프롬프트·업로드 PDF는 OpenAI로 전송되며 API 비용이 발생할 수 있습니다.")

page = st.navigation([
    st.Page("app_pages/Home.py", title="Home", icon=":material/home:", default=True),
    st.Page("app_pages/Chat.py", title="Chat", icon=":material/chat:"),
    st.Page("app_pages/Chatbot.py", title="Chatbot", icon=":material/local_library:"),
    st.Page("app_pages/ChatPDF.py", title="ChatPDF", icon=":material/picture_as_pdf:"),
])
page.run()
