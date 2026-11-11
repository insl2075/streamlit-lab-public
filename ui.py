"""각 페이지가 공유하는 상태 및 채팅 UI."""

import streamlit as st
from openai import APIConnectionError, AuthenticationError, PermissionDeniedError, RateLimitError

from services import stream_text


def require_client():
    client = st.session_state.get("openai_client")
    if client is None:
        st.info("사이드바에서 OpenAI API Key를 입력하고 ‘적용’을 눌러 주세요.")
        st.stop()
    return client


def show_error(error: Exception) -> None:
    # 원본 API 오류에 키/입력 내용이 포함될 수 있으므로 그대로 출력하지 않습니다.
    if isinstance(error, AuthenticationError):
        message = "API Key를 확인해 주세요. 올바른 키를 사이드바에서 다시 적용할 수 있습니다."
    elif isinstance(error, PermissionDeniedError):
        message = "해당 모델 또는 리소스에 대한 API 권한이 없습니다. 프로젝트 권한을 확인해 주세요."
    elif isinstance(error, RateLimitError):
        message = "API 사용 한도 또는 크레딧을 확인하고 잠시 후 다시 시도해 주세요."
    elif isinstance(error, APIConnectionError):
        message = "OpenAI에 연결하지 못했습니다. 네트워크를 확인하고 다시 시도해 주세요."
    elif isinstance(error, (RuntimeError, TimeoutError)):
        message = str(error)
    else:
        message = "요청에 실패했습니다. 모델 접근 권한, 파일 형식, API 사용 한도를 확인해 주세요."
    st.error(message)


def clear_history(key: str) -> None:
    st.session_state[key] = []


def render_chat(client, history_key: str, instructions: str, tools=None,
                placeholder: str = "메시지를 입력하세요") -> None:
    history = st.session_state.setdefault(history_key, [])
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input(placeholder, key=f"{history_key}_input", max_chars=12000)
    if not prompt or not prompt.strip():
        return
    user_message = {"role": "user", "content": prompt.strip()}
    with st.chat_message("user"):
        st.markdown(prompt)
    try:
        with st.chat_message("assistant"):
            answer = st.write_stream(stream_text(client, history + [user_message], instructions, tools))
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError("텍스트 응답이 없습니다. 질문을 다시 입력해 주세요.")
    except Exception as error:
        show_error(error)
        st.caption("불완전한 답변은 대화 기록에 저장하지 않았습니다. 질문을 다시 입력해 주세요.")
        return
    history.extend([user_message, {"role": "assistant", "content": answer}])
