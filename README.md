# 🤖 Entra ID App Guide Chatbot

Azure OpenAI + Azure Cognitive Search + Streamlit 기반 **Entra ID App 가이드 챗봇**  
사내 문서(PDF)를 자동 인덱싱하고, 자연어 질문에 대해 문서 기반 RAG(Retrieval Augmented Generation) 답변을 제공합니다.

---

## 🚀 프로젝트 개요

### 문제점
- 기존 KTAUTH 시스템 Entra App 신청 가이드 문서가 **PDF 형태로만 제공**되어 검색 불편
- 사용자들은 필요한 정보를 빠르게 찾기 어려움

### 해결 방안
- PDF 문서를 Azure Blob Storage에 업로드
- Azure Cognitive Search에서 자동 인덱싱 및 벡터 검색 구성
- Azure OpenAI GPT 모델과 연동해 **질의응답 Chatbot** 제공
- Streamlit UI로 간단히 사내 포털에서 접근 가능

---

## 🛠️ 아키텍처
사용자 ─▶ Streamlit UI ─▶ RAG Chain (Retriever + LLM)
│
├─▶ Azure Cognitive Search (벡터+키워드 검색)
│
└─▶ Azure OpenAI (GPT-4o-mini, Embedding 모델)

문서 소스: Blob Storage (PDF) → Indexer → Search Index

---

## ⚙️ 주요 기능

✅ PDF 문서 자동 인덱싱 (Azure Blob Storage + Indexer)  
✅ 문서 기반 RAG 검색 (벡터 + 키워드 혼합 검색)  
✅ GPT-4o-mini 모델을 이용한 자연어 답변 생성  
✅ Streamlit 기반 UI  
- 좌측 사이드바: 질문 히스토리 관리  
- 메인 영역: 대화형 QA + 답변  
- 📖 버튼 클릭 시 문서 컨텍스트 확인 가능  

---

## 📂 디렉토리 구조
ai_project/
├── app/
│ ├── config.py # 환경설정 로더
│ ├── ingest/
│ │ └── indexer.py # PDF → Azure Search 인덱싱
│ ├── rag/
│ │ ├── retriever.py # Azure Search 문서 검색
│ │ └── chain.py # RAG 체인 (Retriever + LLM)
│ └── ui/
│ └── streamlit_app.py # Streamlit 메인 UI
├── docs/ # PDF 문서 저장
├── .streamlit/
│ └── config.toml # UI 테마 및 옵션
├── .env # 환경 변수 설정
└── README.md

---

## 🔑 환경 변수 (.env 예시)

```env
# ===== Azure OpenAI =====
AOAI_ENDPOINT=https://<리소스명>.openai.azure.com/
AOAI_API_VERSION=2024-12-01-preview
AOAI_DEPLOYMENT=gpt-4o-mini
AOAI_API_KEY=<YOUR_API_KEY>
AOAI_EMBED_DEPLOYMENT=text-embedding-3-small

# ===== Azure Cognitive Search =====
AIS_ENDPOINT=https://<리소스명>.search.windows.net
AIS_API_KEY=<YOUR_SEARCH_KEY>
AIS_INDEX=rag-khchoi
AIS_INDEXER_NAME=rag-khchoi-indexer

# ===== 선택 =====
KEYVAULT_URL=https://<keyvault-name>.vault.azure.net/

📊 데모 스크린샷
1. 챗봇 메인 UI

(예시 스크린샷 추가 가능)

2. 참고 문서 컨텍스트

(문서 일부가 컨텍스트로 표시되는 화면)

🌟 기대 효과

사용자들이 문서 전체를 검색하지 않고도 빠른 답변 획득 가능

사내 Entra App 신청/관리 가이드의 접근성 대폭 향상

향후 확장 가능성:

다국어 지원

추가 문서 자동 인덱싱

보안 로그 및 권한별 접근 제어

👨‍💻 발표자 Note

"문서 기반 AI 검색 서비스"라는 점을 강조

**Azure 생태계(AOAI + Search + Blob)**를 조합한 Best Practice 사례

Streamlit UI는 심플하게 → 누구나 접근 가능