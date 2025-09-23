# 🚀 Entra App Management Copilot – 단계별 로드맵
> 기반 기술: **Azure OpenAI Service, Azure AI Search, Azure AI Vision, Azure Document Intelligence, Microsoft Graph API**

---

## 📌 0단계 — PoC
**목표**  
- FAQ 챗봇 (Streamlit UI → Azure AI Search → Azure OpenAI)  
- 답변과 함께 **Confluence 원문 URL** 표시  
- 구성도 요약(라이트): PDF/이미지 업로드 → OCR → OpenAI 요약 리포트

**산출물**  
- 데모 스크립트 3건 (Entra App 가이드 / OIDC 셋업 / 로그인 오류)  
- 샘플 리포트 (구성요약 + 권한 후보 + 주의사항)

---

## 📌 1단계 — 지식베이스·챗봇 고도화 (2~4주)
**목표**  
- 운영 가능한 RAG 기반 가이드 챗봇  
- Azure AI Search에 Confluence 문서 PDF/이미지 인덱싱  

**주요 기능**  
- Skillset: OCR, language detection, text normalizer  
- 스키마: `title, url, content, embedding`  
- 검색 품질 개선 (synonyms, boosting, k값 튜닝)  
- UX: "관련 문서 더보기", "정확/부정확 피드백" 버튼  

**성과 지표**  
- 답변 정확도 ≥ 80%  
- 평균 응답 속도 ≤ 2.5초  
- 운영비용 추정 리포트 제공  

---

## 📌 2단계 — Azure 구성도 분석 서비스 (4~8주)
**목표**  
- 첨부 다이어그램 → 관리자용 리포트 자동 생성  

**주요 기능**  
- Document Intelligence: 텍스트/표/도형 관계 추출  
- Azure AI Vision: **Azure 리소스 아이콘 식별**  
- AI Search + OpenAI: 구성 설명 + 권한 추천 + 보안 체크  
- 리포트 출력:  
  - 구성 요약  
  - 예상 권한 후보  
  - 보안 주의사항 (예: Public Storage 노출)  

**성과 지표**  
- 관리자 검토 시간 50% 절감  
- 권한 과다 요청 감지율 측정  

---

## 📌 3단계 — Entra App 자동 등록 서비스 (승인 연동) (8~10주)
**목표**  
- 승인 완료 이벤트 기반 **자동 앱 등록**  

**연동 방식**  
- KAUTH 승인 → Webhook 호출 or 승인 테이블 폴링  
- 이벤트 Payload:  
  ```json
  {
    "appName": "SampleApp",
    "owner": "홍길동",
    "redirectUris": ["https://sample/callback"],
    "permissions": ["User.Read"],
    "tenantId": "xxxx-xxxx"
  }
