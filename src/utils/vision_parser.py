"""
vision_parser.py
- Azure AI Vision / Document Intelligence 기반 구성도 분석 뼈대 코드
- PDF/이미지에서 Azure 리소스 추출 및 요약 기능
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
AZURE_VISION_KEY = os.getenv("AZURE_VISION_KEY")

# -------------------------------
# Azure AI Vision OCR (이미지 → 텍스트)
# -------------------------------
def analyze_image_ocr(image_path: str):
    """
    이미지에서 텍스트 추출 (OCR)
    """
    url = f"{AZURE_VISION_ENDPOINT}/computervision/imageanalysis:analyze?api-version=2023-02-01-preview&features=read"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/octet-stream"
    }

    with open(image_path, "rb") as f:
        data = f.read()

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


# -------------------------------
# Azure Document Intelligence (PDF → 구조화 데이터)
# -------------------------------
def analyze_pdf_structure(pdf_path: str):
    """
    PDF에서 텍스트/테이블/레이아웃 추출
    """
    url = f"{AZURE_VISION_ENDPOINT}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version=2023-07-31"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/pdf"
    }

    with open(pdf_path, "rb") as f:
        data = f.read()

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
