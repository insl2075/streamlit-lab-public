import streamlit as st

from ui import clear_history, render_chat, require_client

st.title("Chat")
st.caption("대화 기록을 기억하는 스트리밍 챗봇입니다.")
client = require_client()
st.button("Clear", key="clear_chat", on_click=clear_history, args=("chat_messages",))
render_chat(client, "chat_messages", "도움이 되는 한국어 AI 도우미입니다. 사용자의 언어로 정확하고 친절하게 답하세요.")
