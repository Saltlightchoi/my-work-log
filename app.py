import streamlit as st
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 0. 구글 시트 설정
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
        .main-title { font-size: 2rem !important; font-weight: bold; padding-bottom: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 메뉴 렌더링
# ==========================================
menu_selection = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu_selection == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu_selection == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu_selection == "📊 장비가동데이터":
    EquipmentDataTab(db_equipment).render()
elif menu_selection == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
