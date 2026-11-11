# Streamlit 생성 AI 실습

Streamlit과 OpenAI API를 이용한 질의응답, 이미지 생성, 채팅, PDF 검색 웹 앱입니다.

[앱 실행](https://insl2075-ai-lab.streamlit.app/)

## 바로 실행

Python 3.12 환경에서 `streamlit_app.py`가 있는 폴더에서 실행합니다.

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

브라우저의 사이드바에 본인의 OpenAI API Key를 입력하고 **적용**을 누르세요. 키를 소스 코드, README, GitHub, Secrets에 넣을 필요가 없습니다. 적용은 키를 세션에 설정하는 단계이며 실제 인증과 모델 권한은 요청할 때 확인합니다.

## 들어 있는 기능

| 페이지 | 구현 |
|---|---|
| Home | `gpt-6-luna` Responses API 질의응답, `@st.cache_data`, `gpt-image-2.6-flare` 이미지 생성, Base64 디코딩, spinner, 이미지 다운로드 |
| Chat | `st.session_state` 대화 기록, Clear 콜백, `stream=True`, `st.write_stream` |
| Chatbot | 국립부경대학교 도서관 규정 전체 문자열을 `instructions`에 전달하는 스트리밍 챗봇 |
| ChatPDF | 단일 PDF 업로드, OpenAI File Search, 세션당 검색 저장소 재사용, Clear와 Leave |

공통 진입점은 `streamlit_app.py`, 페이지 폴더는 `pages`가 아닌 `app_pages`입니다. API client는 `st.session_state["openai_client"]`에 저장합니다.

## GitHub Codespaces

1. GitHub에 실습용 저장소를 만듭니다. 과제는 공개 저장소와 README 생성을 요구합니다. 공개해도 되는 코드만 올리고 API Key나 개인 PDF는 올리지 마세요.
2. 이 폴더의 **내용물**을 저장소 루트에 복사합니다. `streamlit_app.py`가 루트에 있어야 아래 배포 경로를 그대로 사용할 수 있습니다.
3. 저장소에서 **Code → Codespaces → Create codespace on main**을 선택합니다.
4. 터미널에서 위 설치/실행 명령을 입력합니다.
5. 8501 포트를 브라우저로 열고 기능을 확인합니다. API Key가 입력된 앱 포트를 불필요하게 공개하지 마세요.
6. 변경사항을 GitHub에 commit/push합니다.

## Streamlit Community Cloud 배포

1. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인합니다.
2. **Create app → Yup, I have an app**을 선택합니다.
3. GitHub 저장소와 업로드한 브랜치를 선택합니다.
4. **Main file path**를 `streamlit_app.py`로 지정합니다. 하위 폴더에 올렸다면 실제 경로를 입력합니다.
5. **Advanced settings**에서 Python 3.12를 선택하고 Secrets는 비워 둡니다.
6. Deploy를 누르고 아래 기능 검사를 수행합니다.
7. 배포된 `https://…streamlit.app` 주소를 과제 제출란에 제출합니다.

## 기능 확인

- [ ] Home: 질문 입력 → 답변 출력 → 같은 질문 재입력 시 캐시 재사용
- [ ] Home: 이미지 프롬프트 입력 → 생성 중 spinner → 이미지 표시/다운로드
- [ ] Chat: “내 이름은 민수야” 다음 “내 이름이 뭐야?” → 이전 대화 활용
- [ ] Chat: 다른 페이지를 다녀와도 기록 유지, Clear 후 기록 삭제
- [ ] Chatbot: 아래 두 테스트 질문에 규정 근거로 답변
- [ ] ChatPDF: PDF 한 개 업로드 → 처리 완료 → 문서에 관한 질의응답
- [ ] ChatPDF: Clear는 대화만 삭제, Leave는 검색 저장소와 원본 파일 삭제 후 업로드 화면 복귀
- [ ] 배포된 URL에서도 위 기능 확인

PDF 예시: [Attention Is All You Need](https://arxiv.org/pdf/1706.03762). “논문의 핵심 아이디어는 무엇인가요?”, “멀티헤드 어텐션을 설명해 주세요”로 확인할 수 있습니다. 실제 PDF를 내려받아 업로드하세요.

## 도서관 질문의 기준 답안과 주의점

2026-11-11에 확인한 공식 웹페이지에서 **규정과 운영세칙의 대출 기준이 다릅니다.** 과제 지시대로 규정 본문을 넣었으므로 챗봇은 규정 기준을 답합니다.

1. **도서관 휴관일은 언제인가요?**
   - 규정 제20조: 자료실은 공휴일과 개교기념일, 일반열람실은 설날과 추석입니다. 도서관장이 필요에 따라 조정할 수 있습니다.
2. **학부생은 책을 몇 권까지 빌릴 수 있나요?**
   - 규정 제22조: 학부생은 **5책 이내, 10일**입니다.
   - 별도로 공개된 운영세칙 별표2에는 **10책, 14일, 연기 2회**로 안내되어 있습니다. 실제 이용 조건은 최신 도서관 안내를 확인하세요.

원문과 개정 표시는 `data/SOURCES.md`에 정리했습니다. `data/library_rules.txt`는 공식 규정 페이지의 본문이며 임의로 대출 수치를 수정하지 않았습니다.

## 보안·비용·정리

- 키는 현재 서버 세션 메모리에만 보관하고 소스 파일/로그에 저장하지 않습니다. 공개 앱 운영자는 실행 환경에 접근할 수 있으므로 신뢰할 수 있는 앱에서만 키를 입력하세요.
- Home 응답 캐시는 임의의 세션 ID로 사용자를 분리하고 최대 15분 보관합니다. API Key 변경 시 새 ID를 사용합니다.
- API 호출과 File Search 저장소는 비용이 발생할 수 있습니다. 현재 [OpenAI 요금](https://developers.openai.com/api/docs/pricing)을 확인하세요.
- PDF 업로드는 **PDF로 대화 시작**을 눌렀을 때만 수행합니다. 권한이 있는 문서만 사용하세요.
- Leave는 이 앱이 만든 검색 저장소와 원본 업로드 파일을 삭제합니다. 삭제 실패 시 리소스 ID를 유지하여 다시 정리할 수 있게 했습니다.
- 탭을 닫기만 하면 삭제를 보장할 수 없습니다. 저장소는 마지막 사용 후 1일 만료로 설정했지만 원본 파일은 남을 수 있으므로 **사용 후 Leave**를 누르세요. 세션을 잃었다면 OpenAI 대시보드에서 해당 리소스를 확인하세요.
- PDF 리소스가 남은 동안 API Key 변경/삭제를 막아 기존 키로 정리할 수 있게 했습니다.
- 자동 API 재시도는 끄고 오류를 안내합니다. 전송 타임아웃 직후 같은 생성 요청을 다시 하면 서버에서 먼저 처리된 요청이 있을 수 있습니다.

## 테스트

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

테스트는 모의 API 응답으로 페이지 전환, 캐시, 채팅 기록, 스트리밍, 키 제거, PDF 저장소 재사용 및 정리를 확인합니다. 실제 모델 호출·이미지 생성·PDF 검색은 API 권한과 크레딧이 있는 키로 별도 확인해야 합니다.

## 파일 구성

```text
streamlit_app.py       공통 사이드바, API client, st.navigation
config.py              모델 이름, 크기 제한, 출처 URL
services.py            캐시, 이미지, 스트리밍, PDF 리소스 관리
ui.py                  공통 채팅 UI, Clear 콜백, 오류 안내
app_pages/
  Home.py
  Chat.py
  Chatbot.py
  ChatPDF.py
data/
  library_rules.txt     공식 규정 본문
  SOURCES.md            출처와 규정/세칙 차이
tests/                 API 비용이 들지 않는 자동 테스트
requirements.txt
requirements-dev.txt
.streamlit/config.toml
.gitignore
```

## 구현 참고 자료

- [OpenAI Responses 스트리밍](https://developers.openai.com/api/docs/guides/streaming-responses)
- [OpenAI File Search](https://developers.openai.com/api/docs/guides/tools-file-search)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [GPT-Image-2.6 Flare](https://developers.openai.com/api/docs/models/gpt-image-2.6-flare)
- [Streamlit navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation)
- [Streamlit cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [Streamlit Community Cloud 배포](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
