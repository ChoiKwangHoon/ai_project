# Python 표준 로깅 라이브러리 불러오기
import logging

# 운영체제 경로 및 디렉토리 관련 작업을 위한 모듈
import os

# 현재 날짜를 문자열로 가져오기 위해 datetime 모듈 불러오기
from datetime import datetime

# 로그를 저장할 디렉토리 이름 지정
LOG_DIR = "logs"

# 디렉토리가 존재하지 않으면 생성 (exist_ok=True → 이미 있어도 에러 안 남)
os.makedirs(LOG_DIR, exist_ok=True)

# 오늘 날짜를 YYYY-MM-DD 형식으로 문자열 생성
today_str = datetime.now().strftime("%Y-%m-%d")

# 로그 파일 이름을 날짜 기반으로 지정 (예: app-2025-09-29.log)
LOG_FILE = os.path.join(LOG_DIR, f"app-{today_str}.log")

# 로거 객체 생성 (이름: entraaid_app)
logger = logging.getLogger("entraaid_app")

# 기본 로그 레벨 설정 (INFO 이상만 기록)
logger.setLevel(logging.INFO)

# ----- 콘솔 핸들러 설정 -----
# 콘솔(터미널)에 로그 출력
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ----- 파일 핸들러 설정 -----
# 지정한 로그 파일에 로그 저장
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.INFO)

# ----- 로그 출력 형식 지정 -----
# 로그 메시지 포맷: [시간][레벨][로거이름] 메시지
formatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s][%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 포맷터를 핸들러에 적용
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 중복 추가 방지: 기존에 핸들러가 없을 때만 등록
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# 외부 모듈에서 logger 객체를 그대로 사용할 수 있도록 제공
__all__ = ["logger"]
