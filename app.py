import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 0. 구글 시트 설정 및 객체 생성
# ==========================================
SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"

# 각 데이터베이스 객체 생성
db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_equipment = DataManager(SPREADSHEET_ID, "장비데이터")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

# ==========================================
# 1. 환경 설정 및 CSS
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 350px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 메뉴 렌더링 및 기능 로직
# ==========================================
menu_selection = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu_selection == "📝 업무일지":
    # 데이터 로드 및 필터링 기능
    df = db_work_log.load()
    
    # 날짜 데이터 형식 변환 (문자열 -> datetime)
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')

    st.sidebar.header("🔍 검색 및 필터링")
    date_range = st.sidebar.date_input("날짜 범위", value=(datetime.now() - timedelta(weeks=2), datetime.now()))
    equip_filter = st.sidebar.multiselect("장비 선택", options=df['장비'].unique())
    keyword = st.sidebar.text_input("내용 검색")

    # 필터 적용
    mask = (df['날짜'].dt.date >= date_range[0]) & (df['날짜'].dt.date <= date_range[1])
    filtered_df = df.loc[mask]
    
    if equip_filter:
        filtered_df = filtered_df[filtered_df['장비'].isin(equip_filter)]
    if keyword:
        filtered_df = filtered_df[filtered_df['업무내용'].str.contains(keyword, na=False)]

    # 렌더링 (필터링된 데이터 전달)
    WorkLogTab(db_work_log).render(filtered_df)

elif menu_selection == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu_selection == "📊 장비가동데이터":
    EquipmentDataTab(db_equipment).render()
elif menu_selection == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
