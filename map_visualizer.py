import folium
from distance_calculator import DistanceCalculator

class MapVisualizer:
    """Folium을 활용하여 기준지와 필지 간의 거리를 시각화하는 클래스"""

    def __init__(self, ref_coords: tuple):
        """
        생성자: 지도의 중심이 될 기준지 좌표를 입력받아 지도를 초기화합니다.
        
        Args:
            ref_coords (tuple): 기준지 위경도 좌표 (위도, 경도)
        """
        self.ref_coords = ref_coords
        
        # 지도 객체 생성 (초기 줌 레벨은 10으로 설정하여 30km 영역이 보이도록 함)
        self.map = folium.Map(location=self.ref_coords, zoom_start=10)
        
        # 기준지 마커 추가 (빨간색 마커)
        folium.Marker(
            location=self.ref_coords,
            popup="<b>📍 기준지</b>",
            icon=folium.Icon(color="red", icon="star"),
            tooltip="기준지"
        ).add_to(self.map)
        
        # 기준지 중심의 반경 1km, 5km, 10km, 20km, 30km 가이드라인 점선 원 추가
        self._add_distance_guidelines()

    def _add_distance_guidelines(self):
        """기준지 중심 반경 1km, 5km, 10km, 20km, 30km 영역에 점선 원(Circle)을 추가합니다."""
        guidelines = [
            {"radius_m": 1000, "label": "1km", "color": "#1F77B4"},
            {"radius_m": 5000, "label": "5km", "color": "#FF7F0E"},
            {"radius_m": 10000, "label": "10km", "color": "#D62728"},
            {"radius_m": 20000, "label": "20km", "color": "#9467BD"},
            {"radius_m": 30000, "label": "30km", "color": "#7F7F7F"}
        ]
        
        for guide in guidelines:
            folium.Circle(
                location=self.ref_coords,
                radius=guide["radius_m"],
                color=guide["color"],
                fill=False,
                weight=1.5,
                opacity=0.6,
                dash_array="6, 6",
                tooltip=f"반경 {guide['label']}"
            ).add_to(self.map)

    def add_parcel(self, parcel_coords: tuple, index: int, address: str, distance_km: float):
        """
        지도에 개별 필지 마커와 기준지-필지 간의 연결선(PolyLine)을 추가합니다.
        거리에 따라 색상을 동적으로 지정합니다:
        - 3km 이하: 초록색 ('green')
        - 3km 초과 ~ 10km 이하: 주황색 ('orange')
        - 10km 초과: 빨간색 ('red')
        
        Args:
            parcel_coords (tuple): 필지의 위경도 좌표 (위도, 경도)
            index (int): 필지 순번 (1부터 시작)
            address (str): 필지 주소
            distance_km (float): 계산된 직선거리 (km)
        """
        name = f"필지 {index}"
        
        # 거리에 따른 색상 맵핑
        color = DistanceCalculator.get_color_by_distance(distance_km)
        
        # 팝업에 표시할 상세 내용 (HTML 형식)
        popup_html = f"""
        <div style="font-family: 'Malgun Gothic', sans-serif; font-size: 13px; line-height: 1.6; min-width: 150px;">
            <strong style="font-size: 14px; color: #333;">🏠 {name}</strong><br/>
            <span style="color: #666;">주소: {address}</span><br/>
            <span style="color: {color}; font-weight: bold;">거리: {distance_km:.2f} km</span>
        </div>
        """
        popup = folium.Popup(popup_html, max_width=300)
        
        # 필지 마커 추가
        folium.Marker(
            location=parcel_coords,
            popup=popup,
            icon=folium.Icon(color=color, icon="home"),
            tooltip=name
        ).add_to(self.map)
        
        # 기준지와 필지 간의 연결선(PolyLine) 추가
        folium.PolyLine(
            locations=[self.ref_coords, parcel_coords],
            color=color,
            weight=2,
            opacity=0.8,
            dash_array="4, 4" if color in ["red", "purple"] else None,
            tooltip=f"{name} - {distance_km:.2f} km"
        ).add_to(self.map)

        # 기준지와 필지 간의 중간 좌표 계산 (라벨 표시용)
        mid_lat = (self.ref_coords[0] + parcel_coords[0]) / 2.0
        mid_lon = (self.ref_coords[1] + parcel_coords[1]) / 2.0

        # 선 색상에 대응하는 선명한 고대비 테두리 Hex 색상 지정
        color_hex_map = {
            "green": "#2ca02c",   # 선명한 초록
            "orange": "#ff7f0e",  # 선명한 주황
            "red": "#d62728",     # 선명한 빨강
            "purple": "#9467bd"   # 선명한 보라
        }
        border_color = color_hex_map.get(color, color)

        # 중간 지점에 거리 라벨(DivIcon) 추가 (고대비 말풍선 스타일로 가시성 극대화)
        folium.Marker(
            location=(mid_lat, mid_lon),
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
                    font-size: 12px;
                    font-weight: 800;
                    color: #111111;
                    background-color: #ffffff;
                    border: 2.5px solid {border_color};
                    border-radius: 20px;
                    padding: 3px 8px;
                    box-shadow: 0px 3px 8px rgba(0, 0, 0, 0.35);
                    white-space: nowrap;
                    text-align: center;
                    transform: translate(-50%, -50%);
                ">
                    {distance_km:.2f} km
                </div>
                """
            )
        ).add_to(self.map)

    def save_map(self, file_path: str):
        """
        완성된 지도를 HTML 파일로 저장합니다.
        
        Args:
            file_path (str): 저장할 파일 경로
        """
        self.map.save(file_path)

    def save_map_as_png(self, html_path: str, png_path: str):
        """
        지도를 HTML로 임시 저장한 후 html2image 라이브러리를 사용하여 PNG 이미지 파일로 저장합니다.
        
        Args:
            html_path (str): 임시 저장할 HTML 파일 경로
            png_path (str): 최종 저장할 PNG 파일 경로
        """
        self.save_map(html_path)
        try:
            from html2image import Html2Image
            # 1200x800 해상도로 캡처
            hti = Html2Image(size=(1200, 800))
            hti.screenshot(html_file=html_path, save_as=png_path)
            print(f"[Info] 지도 PNG 이미지 저장 성공: {png_path}")
        except Exception as e:
            print(f"[Warning] 지도 PNG 이미지 변환 실패 (크롬 브라우저가 없거나 환경 설정 문제): {e}")
