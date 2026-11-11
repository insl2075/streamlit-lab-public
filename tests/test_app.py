from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from services import cached_answer
from test_services import Stream

ROOT = Path(__file__).resolve().parents[1]


def app():
    return AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=10)


def client():
    result = Mock()
    result.api_key = "test-key-not-real"
    result.responses.create.return_value = NS(status="completed", output_text="테스트 답변")
    return result


def signed_in(c):
    at = app()
    with patch("openai.OpenAI", return_value=c):
        at.run()
        at.text_input(key="key_input").set_value("test-key-not-real")
        at.button(key="FormSubmitter:api_key_form-적용").click().run()
    assert not at.exception
    return at


def test_no_key_shows_prompt():
    at = app().run()
    assert not at.exception
    assert any("API Key" in info.value for info in at.info)


def test_home_result_survives_rerun_and_cache():
    cached_answer.clear()
    c = client()
    at = signed_in(c)
    at.text_area[0].set_value("질문")
    at.button(key="FormSubmitter:text_form-답변 생성").click().run()
    assert not at.exception
    assert at.session_state["home_result"] == ("질문", "테스트 답변")
    at.run()
    assert c.responses.create.call_count == 1


def test_chat_navigation_stream_history_and_clear():
    c = client()
    at = signed_in(c)
    at.switch_page("app_pages/Chat.py").run()
    assert not at.exception
    c.responses.create.return_value = Stream([
        NS(type="response.output_text.delta", delta="안녕"), NS(type="response.completed")])
    at.chat_input[0].set_value("내 이름은 민수야").run()
    assert not at.exception
    assert len(at.session_state["chat_messages"]) == 2
    at.switch_page("app_pages/Home.py").run()
    at.switch_page("app_pages/Chat.py").run()
    assert len(at.session_state["chat_messages"]) == 2
    at.button(key="clear_chat").click().run()
    assert at.session_state["chat_messages"] == []


def test_library_and_pdf_pages_load():
    at = signed_in(client())
    at.switch_page("app_pages/Chatbot.py").run()
    assert not at.exception
    assert any("5책" in info.value for info in at.info)
    at.switch_page("app_pages/ChatPDF.py").run()
    assert not at.exception
    assert at.session_state["pdf_resource"] == {}


def test_key_removal():
    c = client()
    at = signed_in(c)
    next(b for b in at.button if b.label == "키와 대화 지우기").click().run()
    assert not at.exception
    assert "openai_client" not in at.session_state
    c.close.assert_called_once()


def test_pdf_clear_keeps_resource_and_leave_cleans():
    c = client()
    at = signed_in(c)
    at.session_state["pdf_resource"] = {"name": "a.pdf", "file_id": "f", "vector_store_id": "v", "ready": True}
    at.session_state["pdf_messages"] = [{"role": "user", "content": "질문"}]
    at.switch_page("app_pages/ChatPDF.py").run()
    assert not at.exception
    at.button(key="clear_pdf").click().run()
    assert at.session_state["pdf_messages"] == []
    assert at.session_state["pdf_resource"]["vector_store_id"] == "v"
    next(b for b in at.button if b.label == "Leave").click().run()
    assert not at.exception
    assert at.session_state["pdf_resource"] == {}
    c.vector_stores.delete.assert_called_once_with("v")
    c.files.delete.assert_called_once_with("f")
