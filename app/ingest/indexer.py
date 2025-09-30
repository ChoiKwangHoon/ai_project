"""
indexer.py : PDF → 청킹 → 임베딩 생성 → Azure Cognitive Search 업로드
- Portal Indexer 대신 직접 임베딩을 생성하고 벡터 필드(text_vector)에 저장
"""

import os
import uuid
import logging
from typing import List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, IndexDocumentsBatch


from openai import AzureOpenAI
from app.config import AppConfig

# PDF 텍스트 추출 (PyPDF2 사용, fitz 제거)
from PyPDF2 import PdfReader

# 로거 설정
logger = logging.getLogger("entraaid_app")
logging.basicConfig(level=logging.INFO)


def load_pdf_text(pdf_path: str) -> List[str]:
    """
    PDF 파일에서 페이지별 텍스트 추출
    """
    reader = PdfReader(pdf_path)
    texts = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            texts.append(text.strip())
        else:
            logger.warning(f"⚠️ {i+1} 페이지에서 텍스트를 추출하지 못했습니다.")
    logger.info(f"✅ PDF 텍스트 추출 완료: 총 {len(texts)} 페이지")
    return texts


def chunk_texts(texts: List[str], max_chunk_size: int = 1000) -> List[str]:
    """
    텍스트를 일정 길이(max_chunk_size) 단위로 청킹
    """
    chunks = []
    for text in texts:
        while len(text) > max_chunk_size:
            chunks.append(text[:max_chunk_size])
            text = text[max_chunk_size:]
        if text:
            chunks.append(text)
    logger.info(f"✅ 청킹 완료: 총 {len(chunks)} 청크 생성")
    return chunks


def embed_texts(chunks: List[str]) -> List[List[float]]:
    """
    Azure OpenAI Embedding API 호출
    """
    client = AzureOpenAI(
        api_key=AppConfig.AOAI_API_KEY,
        api_version=AppConfig.AOAI_API_VERSION,
        azure_endpoint=AppConfig.AOAI_ENDPOINT,
    )

    response = client.embeddings.create(
        model=AppConfig.AOAI_EMBED_DEPLOYMENT,  # .env에 지정한 임베딩 모델
        input=chunks,
    )

    embeddings = [d.embedding for d in response.data]
    logger.info(f"✅ 임베딩 생성 완료: 총 {len(embeddings)} 벡터")
    return embeddings


def upload_to_search(chunks: List[str], embeddings: List[List[float]], pdf_name: str):
    """
    청크 + 임베딩을 Azure Cognitive Search에 업로드
    """
    search_client = SearchClient(
        endpoint=AppConfig.AIS_ENDPOINT,
        index_name=AppConfig.AIS_INDEX,
        credential=AzureKeyCredential(AppConfig.AIS_API_KEY),
    )

    batch = IndexDocumentsBatch()

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc = {
            "chunk_id": f"{pdf_name}_{i}",  # 키: 허용 문자만 사용
            "parent_id": pdf_name,
            "chunk": chunk,
            "title": pdf_name,
            "text_vector": embedding,
        }
        batch = IndexDocumentsBatch()
        batch.add_upload_actions([doc])  # ✅ 리스트로 전달


    result = search_client.index_documents(batch=batch)
    logger.info(f"✅ {len(chunks)}개 문서 업로드 완료")
    print("✅ 업로드 결과:", result)


def index_pdf(pdf_path: str):
    """
    전체 파이프라인 실행
    """
    try:
        logger.info(f"📄 PDF 파일 처리 시작: {pdf_path}")
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

        texts = load_pdf_text(pdf_path)
        chunks = chunk_texts(texts)
        embeddings = embed_texts(chunks)
        upload_to_search(chunks, embeddings, pdf_name)

        logger.info("🎉 인덱싱 파이프라인 완료")

    except Exception as e:
        logger.error(f"❌ 인덱싱 실패: {e}", exc_info=True)
        print(f"❌ 인덱싱 실패: {e}")


# 단독 실행 시 동작
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PDF 파일 인덱싱")
    parser.add_argument("file_path", type=str, help="인덱싱할 PDF 파일 경로")
    args = parser.parse_args()

    index_pdf(args.file_path)
