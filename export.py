import pandas as pd

class DataExporter:
    """분석 완료된 데이터를 CSV 및 Excel 파일로 내보내는 클래스"""

    @staticmethod
    def export_to_csv(df: pd.DataFrame, file_path: str) -> None:
        """
        Pandas DataFrame을 받아 한글 깨짐이 없는 UTF-8-SIG 인코딩으로 CSV 파일을 저장합니다.
        
        Args:
            df (pd.DataFrame): 내보낼 데이터프레임
            file_path (str): 저장할 파일 경로
            
        Raises:
            ValueError: DataFrame이 비어있거나 올바르지 않은 경우 발생.
            IOError: 파일 쓰기 실패 시 발생.
        """
        if df is None or df.empty:
            raise ValueError("내보낼 데이터가 비어있습니다.")
            
        try:
            # index=False 로 행 번호는 저장하지 않음. UTF-8-SIG 인코딩으로 MS Excel 등에서 한글이 깨지지 않게 방지.
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            print(f"[Info] CSV 내보내기 성공: {file_path}")
        except Exception as e:
            raise IOError(f"CSV 파일 저장 중 오류가 발생했습니다: {e}")

    @staticmethod
    def export_to_excel(df: pd.DataFrame, file_path: str) -> None:
        """
        Pandas DataFrame을 받아 openpyxl 라이브러리를 활용해 Excel 파일로 저장합니다.
        
        Args:
            df (pd.DataFrame): 내보낼 데이터프레임
            file_path (str): 저장할 파일 경로
            
        Raises:
            ValueError: DataFrame이 비어있거나 올바르지 않은 경우 발생.
            IOError: 파일 쓰기 실패 시 발생.
        """
        if df is None or df.empty:
            raise ValueError("내보낼 데이터가 비어있습니다.")
            
        try:
            # openpyxl 엔진을 사용하여 Excel로 내보내기
            df.to_excel(file_path, index=False, engine="openpyxl")
            print(f"[Info] Excel 내보내기 성공: {file_path}")
        except Exception as e:
            raise IOError(f"Excel 파일 저장 중 오류가 발생했습니다: {e}")
