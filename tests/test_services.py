import base64
from types import SimpleNamespace as NS
from unittest.mock import Mock

import httpx
import pytest
from openai import NotFoundError

from services import cached_answer, cleanup_pdf, generate_image, index_pdf, stream_text


class Stream:
    def __init__(self, events):
        self.events = events
        self.closed = False

    def __iter__(self):
        return iter(self.events)

    def close(self):
        self.closed = True


def test_cache_isolated_and_reused():
    cached_answer.clear()
    client = Mock()
    client.responses.create.return_value = NS(status="completed", output_text="정답")
    assert cached_answer("user-a", "질문", client) == "정답"
    assert cached_answer("user-a", "질문", client) == "정답"
    assert client.responses.create.call_count == 1
    cached_answer("user-b", "질문", client)
    cached_answer("user-a", "다른 질문", client)
    assert client.responses.create.call_count == 3
    assert client.responses.create.call_args.kwargs["model"] == "gpt-6-luna"


def test_image_model_and_base64():
    client = Mock()
    client.images.generate.return_value = NS(data=[NS(b64_json=base64.b64encode(b"png").decode())])
    assert generate_image(client, "고양이") == b"png"
    client.images.generate.assert_called_once_with(model="gpt-image-2.6-flare", prompt="고양이")


def test_stream_extracts_text_and_closes():
    client = Mock()
    stream = Stream([NS(type="response.created"), NS(type="response.output_text.delta", delta="안녕"),
                     NS(type="response.output_text.delta", delta="하세요"), NS(type="response.completed")])
    client.responses.create.return_value = stream
    assert "".join(stream_text(client, [], "규정", [{"type": "file_search"}])) == "안녕하세요"
    assert stream.closed
    assert client.responses.create.call_args.kwargs["stream"] is True
    assert client.responses.create.call_args.kwargs["tool_choice"] == "required"


@pytest.mark.parametrize("event", ["error", "response.failed", "response.incomplete"])
def test_stream_error_is_not_success(event):
    client = Mock()
    stream = Stream([NS(type=event)])
    client.responses.create.return_value = stream
    with pytest.raises(RuntimeError):
        list(stream_text(client, [], ""))
    assert stream.closed


def test_truncated_stream_is_not_success():
    client = Mock()
    client.responses.create.return_value = Stream([NS(type="response.output_text.delta", delta="부분")])
    with pytest.raises(RuntimeError):
        list(stream_text(client, [], ""))


def not_found():
    return NotFoundError("missing", response=httpx.Response(404, request=httpx.Request("GET", "https://api.openai.com")), body=None)


def test_pdf_index_once_and_reuse():
    client = Mock()
    client.files.create.return_value = NS(id="file-test")
    client.vector_stores.create.return_value = NS(id="vs-test")
    client.vector_stores.files.retrieve.side_effect = not_found()
    client.vector_stores.files.create.return_value = NS(status="completed")
    state = {}
    index_pdf(client, state, b"%PDF-1.4", "a.pdf")
    index_pdf(client, state, b"%PDF-1.4", "a.pdf")
    assert state["ready"]
    assert client.files.create.call_count == 1
    assert client.vector_stores.create.call_count == 1
    assert client.vector_stores.files.create.call_count == 1


def test_pdf_timeout_retains_resources_for_retry():
    client = Mock()
    client.vector_stores.files.retrieve.return_value = NS(status="in_progress")
    state = {"file_id": "file-test", "vector_store_id": "vs-test"}
    with pytest.raises(TimeoutError):
        index_pdf(client, state, b"", "a.pdf", timeout=0)
    client.vector_stores.files.retrieve.return_value = NS(status="completed")
    index_pdf(client, state, b"", "a.pdf")
    client.files.create.assert_not_called()
    client.vector_stores.create.assert_not_called()
    assert state["ready"]


def test_cleanup_deletes_both_and_clears_state():
    client = Mock()
    state = {"file_id": "file-test", "vector_store_id": "vs-test", "ready": True}
    cleanup_pdf(client, state)
    client.vector_stores.delete.assert_called_once_with("vs-test")
    client.files.delete.assert_called_once_with("file-test")
    assert state == {}


def test_partial_cleanup_keeps_failed_id_and_can_retry():
    client = Mock()
    client.files.delete.side_effect = RuntimeError("network")
    state = {"file_id": "file-test", "vector_store_id": "vs-test", "ready": True}
    with pytest.raises(RuntimeError):
        cleanup_pdf(client, state)
    assert "vector_store_id" not in state
    assert state["file_id"] == "file-test"
    assert state["cleanup_pending"] and not state["ready"]
    client.files.delete.side_effect = None
    cleanup_pdf(client, state)
    assert state == {}
    client.vector_stores.delete.assert_called_once()


def test_already_deleted_resources_are_ok():
    client = Mock()
    client.files.delete.side_effect = not_found()
    client.vector_stores.delete.side_effect = not_found()
    state = {"file_id": "file-test", "vector_store_id": "vs-test"}
    cleanup_pdf(client, state)
    assert not state
