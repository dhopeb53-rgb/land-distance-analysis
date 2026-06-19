from geopy.distance import geodesic

class DistanceCalculator:
    """두 위경도 좌표 간의 직선거리를 계산하는 클래스"""

    def calculate_distance(self, coord1: tuple, coord2: tuple) -> float:
        """
        두 위경도 좌표 (위도, 경도) 간의 직선거리를 계산하여 반올림된 km 단위로 반환합니다.
        
        Args:
            coord1 (tuple): 첫 번째 좌표 (위도, 경도)
            coord2 (tuple): 두 번째 좌표 (위도, 경도)
            
        Returns:
            float: km 단위의 두 지점 간 거리 (소수점 둘째 자리까지 반올림)
            
        Raises:
            ValueError: 입력 좌표 형식이 올바르지 않은 경우 발생.
        """
        if not isinstance(coord1, tuple) or not isinstance(coord2, tuple):
            raise ValueError("입력 좌표는 반드시 (위도, 경도) 튜플 형태여야 합니다.")
        
        if len(coord1) != 2 or len(coord2) != 2:
            raise ValueError("좌표 튜플은 (위도, 경도) 2개의 요소를 포함해야 합니다.")

        try:
            # geodesic을 사용하여 km 단위 거리 계산
            dist_km = geodesic(coord1, coord2).kilometers
            # 소수점 둘째 자리까지 반올림
            return round(dist_km, 2)
        except Exception as e:
            raise ValueError(f"거리 계산 중 오류가 발생했습니다: {e}")
        
    @staticmethod
    def get_color_by_distance(distance_km: float) -> str:
        """
        거리에 따라 지도에 표시할 색상을 반환합니다.
        - 3km 이하: 초록색 ('green')
        - 3km 초과 ~ 10km 이하: 주황색 ('orange')
        - 10km 초과: 빨간색 ('red')
        
        Args:
            distance_km (float): km 단위 거리
            
        Returns:
            str: 색상명 문자열 ('green', 'orange', 'red')
        """
        if distance_km <= 3.0:
            return "green"
        elif distance_km <= 10.0:
            return "orange"
        elif distance_km <= 30.0:
            return "red"
        else:
            return "purple"
