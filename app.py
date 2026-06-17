import io
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from config import Config
from geocoder import Geocoder
from distance_calculator import DistanceCalculator
from map_visualizer import MapVisualizer
from export import DataExporter


def parse_excel_to_addresses(df):
    addresses = []
    col_map = {}
    
    # 1. Try to find columns by name (case-insensitive, ignoring whitespace)
    for col in df.columns:
        col_str = str(col).strip().replace(" ", "").lower()
        if '소재지' in col_str or '주소' in col_str:
            col_map['소재지'] = col
        elif '본번' in col_str:
            col_map['본번'] = col
        elif '부번' in col_str:
            col_map['부번'] = col
        elif '산' in col_str:
            col_map['산'] = col

    # 2. Fallback to column indices if not matched by name
    if '소재지' not in col_map and len(df.columns) > 2:
        col_map['소재지'] = df.columns[2]  # Column C (index 2)
    if '산' not in col_map and len(df.columns) > 3:
        col_map['산'] = df.columns[3]  # Column D (index 3)
    if '본번' not in col_map and len(df.columns) > 4:
        col_map['본번'] = df.columns[4]  # Column E (index 4)
    if '부번' not in col_map and len(df.columns) > 5:
        col_map['부번'] = df.columns[5]  # Column F (index 5)

    # 3. Ultimate fallback (use first column as 소재지)
    if '소재지' not in col_map and len(df.columns) > 0:
        col_map['소재지'] = df.columns[0]

    # Parse each row
    for idx, row in df.iterrows():
        base_addr = ""
        if '소재지' in col_map:
            val = row[col_map['소재지']]
            if pd.notna(val):
                base_addr = str(val).strip()
        
        # Skip empty address base
        if not base_addr:
            continue
            
        mountain = ""
        if '산' in col_map:
            val = row[col_map['산']]
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str == "산" or "산" in val_str:
                    mountain = "산"
        
        bunbon_str = ""
        if '본번' in col_map:
            val = row[col_map['본번']]
            if pd.notna(val):
                try:
                    val_num = float(val)
                    if val_num.is_integer():
                        bunbon_str = str(int(val_num))
                    else:
                        bunbon_str = str(val_num)
                except ValueError:
                    bunbon_str = str(val).strip()
                if bunbon_str in ["0", "0.0"]:
                    bunbon_str = ""
                    
        bubon_str = ""
        if '부번' in col_map:
            val = row[col_map['부번']]
            if pd.notna(val):
                try:
                    val_num = float(val)
                    if val_num.is_integer():
                        bubon_str = str(int(val_num))
                    else:
                        bubon_str = str(val_num)
                except ValueError:
                    bubon_str = str(val).strip()
                if bubon_str in ["0", "0.0"]:
                    bubon_str = ""

        # Assemble address
        full_addr = base_addr
        if mountain:
            full_addr += f" {mountain}"
        if bunbon_str:
            full_addr += f" {bunbon_str}"
            if bubon_str:
                full_addr += f"-{bubon_str}"
                
        # Clean double spaces
        full_addr = " ".join(full_addr.split())
        addresses.append(full_addr)
        
    return addresses


# 1. 페이지 설정 및 프리미엄 스타일 지정
st.set_page_config(
    page_title="토지 필지-기준지 직선거리 분석 시스템",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS를 통한 UI/UX 강화 (그라데이션 타이틀, 카드 스타일, 세련된 레이아웃)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', 'Outfit', sans-serif;
        }
        
        /* 메인 그라데이션 타이틀 */
        .main-title {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 10px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        }
        
        .sub-title {
            color: #555;
            font-size: 1.1rem;
            margin-bottom: 25px;
        }
        
        /* 프리미엄 카드 디자인 */
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #2a5298;
            margin-bottom: 15px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #777;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 1.8rem;
            color: #2a5298;
            font-weight: 700;
            margin-top: 5px;
        }
        
        /* 구분선 스타일 */
        hr {
            margin-top: 2rem;
            margin-bottom: 2rem;
            border: 0;
            border-top: 1px solid rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# 2. 세션 상태 초기화 (입력값 유지 및 동적 반영용)
if "ref_address" not in st.session_state:
    st.session_state.ref_address = ""

if "parcel_data" not in st.session_state:
    # 사용자가 직접 타이핑하거나 붙여넣을 수 있도록 빈 주소 컬럼 데이터프레임 초기화
    st.session_state.parcel_data = pd.DataFrame(columns=["주소"])

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# 3. 사이드바 - 설정 영역 (API 키 및 유틸리티 설정 유지)
st.sidebar.markdown("<h2 style='color: #2a5298; font-weight: 700;'>⚙️ 시스템 설정</h2>", unsafe_allow_html=True)

# API 키 입력
default_api_key = Config.KAKAO_API_KEY if Config.KAKAO_API_KEY else ""
kakao_api_key = st.sidebar.text_input(
    "카카오 REST API 키",
    value=default_api_key,
    type="password",
    help="카카오 Developers에서 발급받은 REST API 키를 입력해 주세요."
)

st.sidebar.markdown("---")
# 버전 표시
st.sidebar.markdown("<div style='font-size: 0.85rem; color: #888; text-align: left; margin-top: 60vh;'>ver 1.0</div>", unsafe_allow_html=True)

# 4. 메인 화면 구성
st.markdown("<h1 class='main-title'>📍 토지 필지-기준지 직선거리 분석</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>대상 필지 주소를 입력하면 기준지와의 직선거리를 계산하고 지도 상에 동적으로 시각화합니다.</p>", unsafe_allow_html=True)

# 5. 기준지 설정 (메인 화면 상단 배치)
st.markdown("<h3 style='font-size: 1.3rem; font-weight: 700; margin-top: 20px;'>📍 기준지 설정</h3>", unsafe_allow_html=True)
ref_address_input = st.text_input(
    "기준지 주소",
    value=st.session_state.ref_address,
    placeholder="예: 경기도 평택시 경기대로 245",
    help="분석 기준이 될 중심지의 주소를 입력하세요."
)
st.session_state.ref_address = ref_address_input

st.markdown("<br/>", unsafe_allow_html=True)

# 6. [신규 기능] 엑셀 파일 일괄 입력 영역
st.markdown("<h3 style='font-size: 1.3rem; font-weight: 700;'>📂 엑셀 파일 업로드 (일괄 입력)</h3>", unsafe_allow_html=True)
st.markdown("""
    * **지번 조립 입력**: `소재지` (C열), `산` 여부 (D열), `본번` (E열), `부번` (F열) 컬럼 데이터를 조합해 주소를 자동 완성합니다. (B열 체크박스 컬럼은 무시됩니다)
    * **일반 주소 목록**: 단일 시트에 `주소` 또는 `소재지` 컬럼만 있는 경우에도 자동으로 필지 목록으로 가져옵니다.
    * **다중 시트 분할 (형식 A)**: `기준지` 시트와 `대상필지` 시트가 있는 경우 각 시트에서 자동으로 주소를 추출합니다.
""")

uploaded_file = st.file_uploader("엑셀 파일 선택 (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state.last_uploaded_file != file_id:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names_clean = [str(s).strip() for s in xls.sheet_names]
            
            # 형식 A 검출 (시트 분할)
            if '기준지' in sheet_names_clean and '대상필지' in sheet_names_clean:
                ref_sheet = [s for s in xls.sheet_names if str(s).strip() == '기준지'][0]
                parcels_sheet = [s for s in xls.sheet_names if str(s).strip() == '대상필지'][0]
                
                # 기준지는 header 없이 첫 셀을 바로 가져옴
                ref_df = pd.read_excel(xls, ref_sheet, header=None)
                if not ref_df.empty:
                    st.session_state.ref_address = str(ref_df.iloc[0, 0]).strip()
                
                parcels_df = pd.read_excel(xls, parcels_sheet)
                addresses = parse_excel_to_addresses(parcels_df)
                if addresses:
                    st.session_state.parcel_data = pd.DataFrame({"주소": addresses})
                    st.success("📂 형식 A(시트 분할) 엑셀 파일 로드 완료!")
                else:
                    st.error("❌ '대상필지' 시트에서 유효한 주소를 찾을 수 없습니다.")
            
            # 단일 시트
            else:
                df_excel = pd.read_excel(uploaded_file)
                col_names_clean = [str(c).strip() for c in df_excel.columns]
                
                # 형식 B (구분 컬럼 존재)
                if '구분' in col_names_clean:
                    gubun_col = [c for c in df_excel.columns if str(c).strip() == '구분'][0]
                    addr_col_candidates = [c for c in df_excel.columns if str(c).strip() in ['주소', '소재지']]
                    addr_col = addr_col_candidates[0] if addr_col_candidates else df_excel.columns[1]
                    
                    ref_rows = df_excel[df_excel[gubun_col].astype(str).str.strip() == '기준지']
                    if not ref_rows.empty:
                        st.session_state.ref_address = str(ref_rows.iloc[0][addr_col]).strip()
                    
                    parcel_rows = df_excel[df_excel[gubun_col].astype(str).str.strip() == '필지']
                    if not parcel_rows.empty:
                        addresses = parse_excel_to_addresses(parcel_rows)
                    else:
                        other_rows = df_excel[df_excel[gubun_col].astype(str).str.strip() != '기준지']
                        addresses = parse_excel_to_addresses(other_rows)
                    
                    if addresses:
                        st.session_state.parcel_data = pd.DataFrame({"주소": addresses})
                        st.success("📂 형식 B(구분 컬럼) 엑셀 파일 로드 완료!")
                    else:
                        st.error("❌ 필지 데이터를 찾을 수 없습니다.")
                
                # 형식 C 및 사용자 정의 지번 조립 형식
                else:
                    addresses = parse_excel_to_addresses(df_excel)
                    if addresses:
                        st.session_state.parcel_data = pd.DataFrame({"주소": addresses})
                        st.success("📂 엑셀 파일에서 필지 주소 로드 완료!")
                    else:
                        st.error("❌ 엑셀 파일에서 유효한 주소 데이터를 찾을 수 없습니다.")
            
            # 세션 상태 업데이트 및 리런 실행
            st.session_state.last_uploaded_file = file_id
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 엑셀 파일을 처리하는 중에 에러가 발생했습니다: {e}")
else:
    if st.session_state.last_uploaded_file is not None:
        st.session_state.last_uploaded_file = None

st.markdown("<br/>", unsafe_allow_html=True)

# 7. 대상 필지 입력 영역 (필지명 없이 '주소'만 입력하는 테이블)
st.markdown("<h3 style='font-size: 1.3rem; font-weight: 700;'>📋 대상 필지 목록 입력</h3>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 0.9rem; color: #666;'>아래 주소 입력창에 필지 주소를 자유롭게 입력해 주세요. (행 추가/삭제 및 복사/붙여넣기 지원)</p>", unsafe_allow_html=True)

# st.data_editor를 사용하여 주소만 있는 대화형 그리드 제공
edited_df = st.data_editor(
    st.session_state.parcel_data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "주소": st.column_config.TextColumn("주소", help="필지의 주소를 입력하세요.", required=True, width="large")
    }
)
st.session_state.parcel_data = edited_df

# 실행 버튼
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    run_analysis = st.button("⚡ 분석 실행", use_container_width=True, type="primary")

st.markdown("<hr/>", unsafe_allow_html=True)

# 8. 분석 프로세스 수행 및 결과 시각화
if run_analysis:
    # 데이터 유효성 검증
    valid_parcels = edited_df.dropna(subset=["주소"])
    valid_parcels = valid_parcels[valid_parcels["주소"].str.strip() != ""]
    
    if not ref_address_input.strip():
        st.error("기준지 주소가 비어있습니다. 주소를 정확히 입력해 주세요.")
    elif valid_parcels.empty:
        st.error("분석할 필지 데이터가 없습니다. 주소를 입력해 주세요.")
    elif not kakao_api_key.strip():
        st.error("카카오 REST API 키가 입력되지 않았습니다. 사이드바에서 확인해 주세요.")
    else:
        with st.spinner("좌표 변환 및 거리 연산 진행 중..."):
            try:
                # 모듈 초기화
                geocoder = Geocoder(api_key=kakao_api_key)
                calculator = DistanceCalculator()
                
                # 기준지 좌표 획득
                ref_coords = geocoder.address_to_coords(ref_address_input)
                
                # 지도 시각화 모듈 초기화 (기준지 좌표만 전달)
                visualizer = MapVisualizer(ref_coords)
                
                # 결과 기록용 리스트
                results = []
                
                # 주소 변환 진행 현황 표시를 위한 progress bar
                progress_bar = st.progress(0.0)
                total_items = len(valid_parcels)
                
                for idx, (_, row) in enumerate(valid_parcels.iterrows(), 1):
                    addr = row["주소"]
                    name = f"필지 {idx}"
                    
                    try:
                        # 좌표 획득
                        parcel_coords = geocoder.address_to_coords(addr)
                        # 거리 계산
                        distance = calculator.calculate_distance(ref_coords, parcel_coords)
                        
                        # 지도에 추가 (index 번호 전달)
                        visualizer.add_parcel(parcel_coords, idx, addr, distance)
                        
                        # 데이터 추가
                        results.append({
                            "구분": name,
                            "주소": addr,
                            "위도": parcel_coords[0],
                            "경도": parcel_coords[1],
                            "거리(km)": distance
                        })
                    except Exception as e:
                        st.warning(f"⚠️ '{name}' 주소 변환 중 오류 발생: {e}")
                    
                    # 프로그레스 업데이트
                    progress_bar.progress(idx / total_items)
                
                progress_bar.empty()
                
                if not results:
                    st.error("모든 필지의 주소 변환에 실패했습니다. 입력 주소를 확인해 주세요.")
                else:
                    # 데이터프레임 변환 및 거리순 정렬
                    res_df = pd.DataFrame(results)
                    res_df_sorted = res_df.sort_values(by="거리(km)", ascending=True).reset_index(drop=True)
                    
                    # 레이아웃 분할 (좌측: 지도 시각화, 우측: 분석 통계 및 결과 테이블)
                    col_map, col_table = st.columns([3, 2])
                    
                    with col_map:
                        st.markdown("<h4 style='font-weight: 700; margin-bottom:15px;'>🗺️ 거리 시각화 지도</h4>", unsafe_allow_html=True)
                        # streamlit-folium을 통해 지도 출력
                        st_folium(visualizer.map, width="100%", height=500, returned_objects=[])
                        st.markdown("""
                            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e9ecef; margin-top: 10px;">
                                <h5 style="margin-top: 0; margin-bottom: 10px; font-size: 0.95rem; font-weight: 700; color: #333;">💡 지도 가이드 및 범례</h5>
                                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.85rem; color: #555;">
                                    <div>
                                        <strong>⭕ 기준지 중심 반경 (점선 원):</strong><br>
                                        <span style="color: #1F77B4;">🔵 1km</span> | 
                                        <span style="color: #FF7F0E;">🟠 5km</span> | 
                                        <span style="color: #D62728;">🔴 10km</span> | 
                                        <span style="color: #9467BD;">🟣 20km</span> | 
                                        <span style="color: #7F7F7F;">⚫ 30km</span>
                                    </div>
                                    <div style="margin-top: 5px;">
                                        <strong>🛣️ 직선 연결선 색상 (거리 구분):</strong><br>
                                        <span style="color: #2ca02c; font-weight: bold;">🟢 초록색</span>: 3km 이하 (인접) <br>
                                        <span style="color: #ff7f0e; font-weight: bold;">🟠 주황색</span>: 3km 초과 ~ 10km 이하 (중거리) <br>
                                        <span style="color: #d62728; font-weight: bold;">🔴 빨간색 (점선)</span>: 10km 초과 (원거리)
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        st.info("💡 우측 하단의 'HTML 지도 다운로드' 버튼으로 전체화면 인터랙티브 지도를 소장하거나 브라우저 캡처 기능을 사용할 수 있습니다.")
                        
                    with col_table:
                        st.markdown("<h4 style='font-weight: 700; margin-bottom:15px;'>📊 거리 통계 및 데이터</h4>", unsafe_allow_html=True)
                        
                        # 통계 요약 카드형 배치
                        avg_dist = res_df_sorted["거리(km)"].mean()
                        min_dist_row = res_df_sorted.iloc[0]
                        max_dist_row = res_df_sorted.iloc[-1]
                        
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        with col_stat1:
                            st.markdown(f"""
                                <div class="metric-card" style="border-left-color: #2ca02c;">
                                    <div class="metric-label">최단 거리 ({min_dist_row['구분']})</div>
                                    <div class="metric-value">{min_dist_row['거리(km)']:.2f} <span style="font-size:1.1rem;">km</span></div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col_stat2:
                            st.markdown(f"""
                                <div class="metric-card" style="border-left-color: #1f77b4;">
                                    <div class="metric-label">평균 거리</div>
                                    <div class="metric-value">{avg_dist:.2f} <span style="font-size:1.1rem;">km</span></div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col_stat3:
                            st.markdown(f"""
                                <div class="metric-card" style="border-left-color: #d62728;">
                                    <div class="metric-label">최장 거리 ({max_dist_row['구분']})</div>
                                    <div class="metric-value">{max_dist_row['거리(km)']:.2f} <span style="font-size:1.1rem;">km</span></div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # 분석 결과 테이블
                        st.dataframe(
                            res_df_sorted,
                            use_container_width=True,
                            column_config={
                                "거리(km)": st.column_config.NumberColumn("거리(km)", format="%.2f km"),
                                "위도": st.column_config.NumberColumn("위도", format="%.6f"),
                                "경도": st.column_config.NumberColumn("경도", format="%.6f")
                            }
                        )
                        
                        # 데이터 내보내기 및 다운로드 구현
                        st.markdown("<h5 style='font-weight: 700; margin-top:20px;'>📥 데이터 다운로드</h5>", unsafe_allow_html=True)
                        
                        col_dl1, col_dl2, col_dl3, col_dl4 = st.columns(4)
                        
                        # CSV 인코딩 변환
                        csv_data = res_df_sorted.to_csv(index=False, encoding="utf-8-sig")
                        with col_dl1:
                            st.download_button(
                                label="CSV 다운로드",
                                data=csv_data,
                                file_name="result_data.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                            
                        # Excel 바이트 변환
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                            res_df_sorted.to_excel(writer, index=False)
                        excel_data = excel_buffer.getvalue()
                        
                        with col_dl2:
                            st.download_button(
                                label="Excel 다운로드",
                                data=excel_data,
                                file_name="result_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            
                        # PNG 지도 이미지 생성 및 변환
                        png_data = b""
                        try:
                            visualizer.save_map_as_png("result_map.html", "result_map.png")
                            with open("result_map.png", "rb") as f:
                                png_data = f.read()
                        except Exception:
                            pass
                            
                        with col_dl3:
                            st.download_button(
                                label="지도 PNG 다운로드",
                                data=png_data,
                                file_name="result_map.png",
                                mime="image/png",
                                use_container_width=True
                            )
                            
                        # HTML 지도 데이터 변환
                        try:
                            html_data = visualizer.map.get_root().render()
                        except Exception:
                            html_data = ""
                            
                        with col_dl4:
                            st.download_button(
                                label="지도 HTML 다운로드",
                                data=html_data,
                                file_name="result_map.html",
                                mime="text/html",
                                use_container_width=True
                            )
                            
                    st.success("🎉 분석이 완료되었습니다. 지도상의 마커를 클릭하여 팝업 정보를 확인해 보세요!")
            
            except Exception as e:
                st.error(f"분석 진행 중 치명적인 에러가 발생했습니다: {e}")
