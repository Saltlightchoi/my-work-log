import streamlit as st
# (삭제됨) from github import Github 

# ==========================================
# ★ 모듈(클래스) 수입
# ==========================================
try:
    from config import DataManager
    from tab_work_log import WorkLogTab
    from tab_cs_check import CSCheckSheetTab
    from tab_equipment_data import EquipmentDataTab
    from tab_ecn_stn import ECNSTNTab
except ModuleNotFoundError as e:
    st.error(f"🚨 **모듈 로드 실패:** `{e.name}.py` 파일을 찾을 수 없습니다.")
    st.stop()

# ==========================================
# 0. 구글 시트 설정 (본인의 시트 ID를 입력하세요)
# ==========================================
SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA" # 구글 시트 URL의 긴 ID

# 각 데이터베이스 객체 생성 (이제 Github 대신 구글 시트 ID를 넘깁니다)
db_work_log = DataManager(SPREADSHEET_ID, "업무일지")
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_equipment = DataManager(SPREADSHEET_ID, "장비데이터")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

# ==========================================
# 1. 환경 설정 및 전체 디자인 (CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 350px !important; }
        .main-title { font-size: 2rem !important; font-weight: bold; padding-bottom: 15px !important; }
    </style>
""", unsafe_allow_html=True)

# ... (기존 로그인 로직 등 유지) ...

# ==========================================
# 2. 메뉴 렌더링 (수정된 객체 전달)
# ==========================================
menu_selection = st.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu_selection == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu_selection == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu_selection == "📊 장비가동데이터":
    EquipmentDataTab(db_equipment).render()
elif menu_selection == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
