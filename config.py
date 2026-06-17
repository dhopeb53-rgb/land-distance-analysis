import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (현재 파일 위치 기준)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """시스템 전반에 사용되는 설정 정보를 관리하는 클래스"""
    
    # 카카오 REST API 키 로드 (없는 경우 공백 문자열 설정, 웹 UI 또는 직접 입력 지원)
    KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")
    
    # 카카오 주소 검색 API URL
    KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
