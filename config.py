import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (현재 파일 위치 기준)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """시스템 전반에 사용되는 설정 정보를 관리하는 클래스"""
    
    # 카카오 REST API 키 로드 및 검증
    KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
    
    if not KAKAO_API_KEY:
        raise ValueError(
            "API 키 에러: .env 파일에 'KAKAO_API_KEY'가 정의되어 있지 않거나 올바르지 않습니다. "
            "프로젝트 루트에 .env 파일을 확인해 주세요."
        )
    
    # 카카오 주소 검색 API URL
    KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
