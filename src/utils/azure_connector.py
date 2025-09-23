"""
azure_connector.py
- Azure Cognitive Search & Graph API 연동 뼈대 코드
- 이후 AI Search 인덱싱, Graph API 기반 Entra App 자동 등록 기능 확장용
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Azure AI Search 설정 (환경변수에서 로드)
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "entra-index")

# Microsoft Graph API 설정 (환경변수에서 로드)
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")


# -------------------------------
# Azure AI Search API 호출 예시
# -------------------------------
def search_documents(query: str, top: int = 5):
    """
    Azure AI Search에서 문서 검색
    """
    url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{AZURE_SEARCH_INDEX}/docs/search?api-version=2021-04-30-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_SEARCH_KEY
    }
    payload = {
        "search": query,
        "top": top
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# -------------------------------
# Microsoft Graph API 인증 토큰
# -------------------------------
def get_graph_token():
    """
    Graph API 호출을 위한 OAuth2 토큰 발급
    """
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default"
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        return None
