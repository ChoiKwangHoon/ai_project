from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_dummy_pdf(filename="entra_app_guide.pdf"):
    """
    간단한 Entra App 가이드 내용을 담은 테스트용 PDF 생성
    """
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 제목
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Entra App Guide (Dummy PDF)")

    # 본문 내용
    c.setFont("Helvetica", 12)
    lines = [
        "1. Entra App 신청 절차",
        "   - KAUTH 시스템에서 신청",
        "   - 관리자 승인 후 등록",
        "",
        "2. OIDC 인증 설정",
        "   - Client ID, Secret 발급",
        "   - Redirect URI 등록",
        "",
        "3. 권한 요청 예시",
        "   - User.Read: 사용자 프로필 조회",
        "   - Mail.Read: 메일 읽기 권한",
        "",
        "4. 개발 환경 설정",
        "   - 로컬 환경에서 OIDC 모듈 다운로드",
        "   - Azure Portal 연동 확인",
    ]

    y = height - 100
    for line in lines:
        c.drawString(50, y, line)
        y -= 20

    c.showPage()
    c.save()
    print(f"✅ Dummy PDF 생성 완료: {filename}")

if __name__ == "__main__":
    create_dummy_pdf()
