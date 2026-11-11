import streamlit as st

from services import cached_answer, generate_image
from ui import require_client, show_error

st.title("Home")
st.write("질문에 답하고, 프롬프트로 이미지를 만들어 보세요.")
client = require_client()

st.subheader("텍스트 생성")
with st.form("text_form"):
    prompt = st.text_area("질문", placeholder="Streamlit의 Session State를 쉽게 설명해 줘.", max_chars=12000)
    submitted = st.form_submit_button("답변 생성", type="primary")
if submitted:
    if not prompt.strip():
        st.warning("질문을 입력해 주세요.")
    else:
        try:
            with st.spinner("답변을 생성하고 있어요…"):
                answer = cached_answer(st.session_state.cache_session_id, prompt.strip(), client)
            st.session_state.home_result = (prompt.strip(), answer)
        except Exception as error:
            show_error(error)
if result := st.session_state.get("home_result"):
    st.caption(f"질문: {result[0]}")
    st.markdown(result[1])
st.caption("같은 질문은 현재 세션의 캐시에서 최대 15분 동안 재사용합니다.")

st.divider()
st.subheader("이미지 생성")
with st.form("image_form"):
    image_prompt = st.text_area("이미지 프롬프트", placeholder="바닷가 도서관에서 책을 읽는 고양이, 수채화 스타일", max_chars=12000)
    generate = st.form_submit_button("이미지 생성", type="primary")
if generate:
    if not image_prompt.strip():
        st.warning("이미지 프롬프트를 입력해 주세요.")
    else:
        try:
            with st.spinner("이미지를 생성하고 있어요. 수십 초 이상 걸릴 수 있어요…"):
                data = generate_image(client, image_prompt.strip())
            st.session_state.home_image = (image_prompt.strip(), data)
        except Exception as error:
            show_error(error)
if result := st.session_state.get("home_image"):
    st.image(result[1], caption=result[0])
    st.download_button("이미지 다운로드", result[1], file_name="generated_image.png", mime="image/png")
