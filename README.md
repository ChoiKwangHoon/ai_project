# 🚀 Entra App Management Copilot

> **목표**  
> 사내 KTAUTH 시스템과 Entra ID App 관리를 **Azure AI 기반**으로 효율화합니다.  


---

## 📌 아키텍처 개요

- **FAQ 챗봇**: Confluence 가이드 문서를 기반으로 RAG + Azure OpenAI  
- **Azure 구성도 분석**: PDF/이미지 → Azure AI Vision + Document Intelligence → 설명/권한 추천  
- **Entra App 자동 등록**: KAUTH 승인 → Webhook 이벤트 → Microsoft Graph API로 자동 앱 생성  
- **대시보드**: Power BI + Log Analytics → 신청 현황, 보안 경고, FAQ 피드백

---

## 📍 단계별 로드맵

### 0단계 — PoC 
- Streamlit 기반 FAQ 챗봇 (Azure AI Search + OpenAI)  
- 답변 + Confluence 원문 URL 표시  
- 구성도 요약(라이트): 첨부 PDF/이미지 → OCR → OpenAI 요약  

### 1단계 — 지식베이스·챗봇 고도화 (2~4주)
- Azure AI Search에 Confluence 문서/이미지 인덱싱  
- Synonyms/Boosting 적용, k값 최적화  
- UI에 “관련 문서 더보기” / “피드백 버튼” 추가  

### 2단계 — Azure 구성도 분석 서비스 (4~8주)
- Document Intelligence로 텍스트/도형 추출  
- Azure AI Vision으로 리소스 아이콘 식별 (VM, App Service 등)  
- OpenAI + AI Search로 **구성 요약/권한 추천/보안 주의사항** 생성  
- KAUTH 신청서 UI에 리포트 탭 추가  

### 3단계 — Entra App 자동 등록 서비스 (승인 연동) (8~10주)
- 승인 이벤트(Webhook) → Azure Function/Container App → Microsoft Graph API 호출  
- 앱 생성 + 권한 매핑 + Redirect URI 등록  
- 아이템포턴시 키로 중복 방지  
- 실패 시 알림 및 롤백 처리  

### 4단계 — 운영/확장 (10~12주+)
- Power BI 대시보드 (신청량, 실패율, 보안 경고)  
- 챗봇 피드백 기반 문서 자동 개선  
- 보안 고도화 (민감 권한 요청 시 추가 근거 요구)  
- 사내 레지스트리로 OIDC 모듈 배포, 샘플 앱 템플릿 제공  

---

## 🌐 네트워크 시나리오

### 시나리오 A — 대외 통신 허용
- On-Prem → API Management(Private Endpoint) → Azure OpenAI / AI Search / Storage  

### 시나리오 B — 대외 통신 불가
- DMZ API Gateway 개방, 내부는 프록시 경유  
- 승인 이벤트만 Outbound 단일 경로 허용  
- ExpressRoute or Site-to-Site VPN 사용 가능  

---

## 🎯 평가 기준 매핑

- **기능 구현**: 챗봇 → 구성도 분석 → 자동 등록(승인 연동)  
- **기술 구현**: AI Search 스키마 최적화, Graph API 아이템포턴시/재시도  
- **UX**: 출처 URL, 리포트 탭, 피드백 루프, 대시보드  
- **발표/데모**: 실시간 챗봇, 첨부 분석 리포트, 승인 이벤트 → 자동 등록 시연  
- **혁신성/확장성**: 다이어그램 인식 + 권한 추천 + 정책 위반 감지 → Copilot 지향  

---

## 📦 실행 방법 (PoC 기준)

```bash
# 1. Python 3.12 가상환경 생성
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정 (.env)
OPENAI_API_KEY=sk-xxxxxx

# 4. 실행
streamlit run app.py
