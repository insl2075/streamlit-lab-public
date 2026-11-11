"""OpenAI 호출. API Key는 파일/환경 변수에 저장하지 않습니다."""

import base64
import time
from collections.abc import Iterator

import streamlit as st
from openai import NotFoundError

from config import IMAGE_MODEL, TEXT_MODEL


@st.cache_data(ttl=900, max_entries=128, show_spinner=False)
def cached_answer(session_id: str, prompt: str, _client, model: str = TEXT_MODEL) -> str:
    # client는 해시 대상에서 제외하고, 임의의 세션 ID로 사용자별 캐시를 분리합니다.
    # API Key 변경 시 session_id도 교체하므로 이전 사용자의 결과가 섞이지 않습니다.
    response = _client.responses.create(model=model, input=prompt, store=False)
    if response.status != "completed" or not response.output_text:
        raise RuntimeError("텍스트 응답을 완성하지 못했습니다. 다시 시도해 주세요.")
    return response.output_text


def generate_image(client, prompt: str) -> bytes:
    image = client.images.generate(model=IMAGE_MODEL, prompt=prompt)
    if not image.data or not image.data[0].b64_json:
        raise RuntimeError("이미지 데이터가 없습니다.")
    return base64.b64decode(image.data[0].b64_json, validate=True)


def stream_text(client, messages: list, instructions: str, tools=None) -> Iterator[str]:
    kwargs = dict(model=TEXT_MODEL, input=messages, instructions=instructions,
                  stream=True, store=False)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "required"
    stream = client.responses.create(**kwargs)
    completed = False
    try:
        for event in stream:
            if event.type in ("response.output_text.delta", "response.refusal.delta"):
                yield event.delta
            elif event.type == "response.completed":
                completed = True
            elif event.type in ("error", "response.failed", "response.incomplete"):
                raise RuntimeError("응답 생성이 중단되었습니다. 잠시 후 다시 질문해 주세요.")
        if not completed:
            raise RuntimeError("연결이 끊겨 응답을 완성하지 못했습니다.")
    finally:
        stream.close()


def index_pdf(client, state: dict, data: bytes, name: str, timeout: float = 180) -> None:
    """같은 세션에서 이미 만들어진 리소스는 재사용합니다."""
    if state.get("ready"):
        return
    if not state.get("file_id"):
        result = client.files.create(file=(name, data, "application/pdf"), purpose="assistants")
        state["file_id"] = result.id
    if not state.get("vector_store_id"):
        result = client.vector_stores.create(
            name=f"Streamlit Lab: {name}",
            expires_after={"anchor": "last_active_at", "days": 1},
        )
        state["vector_store_id"] = result.id
    store_id, file_id = state["vector_store_id"], state["file_id"]
    # 재실행/타임아웃 후에도 먼저 조회하여 동일한 파일을 중복 등록하지 않습니다.
    try:
        result = client.vector_stores.files.retrieve(file_id, vector_store_id=store_id)
    except NotFoundError:
        result = client.vector_stores.files.create(vector_store_id=store_id, file_id=file_id)
    deadline = time.monotonic() + timeout
    while result.status == "in_progress":
        if time.monotonic() >= deadline:
            raise TimeoutError("PDF 처리 시간이 길어지고 있습니다. ‘처리 재확인’을 눌러 주세요.")
        time.sleep(1)
        result = client.vector_stores.files.retrieve(file_id, vector_store_id=store_id)
    if result.status != "completed":
        raise RuntimeError("PDF 인덱싱에 실패했습니다. Leave로 정리 후 다른 PDF를 사용해 주세요.")
    state["ready"] = True


def cleanup_pdf(client, state: dict) -> None:
    """앱이 생성한 vector store와 원본 파일만 삭제. 실패한 ID는 재시도용으로 유지."""
    state["cleanup_pending"] = True
    state["ready"] = False
    for key, api in (("vector_store_id", client.vector_stores), ("file_id", client.files)):
        resource_id = state.get(key)
        if resource_id:
            try:
                api.delete(resource_id)
            except NotFoundError:
                pass  # 이전 요청에서 이미 삭제된 경우도 완료로 처리합니다.
            state.pop(key, None)
    state.clear()
