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

db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_equipment = DataManager(SPREADSHEET_ID, "장비데이터")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

# ==========================================
# 1. 환경 설정 및 로그인 로직
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

if st.session_state['user_name'] is None:
    st.markdown("<h2 style='text-align: center;'>🔐 장비 관리 통합 시스템 로그인</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        user_input = st.text_input("👤 사용자 이름")
        if st.form_submit_button("로그인"):
            if user_input.strip():
                st.session_state['user_name'] = user_input.strip()
                st.rerun()
    st.stop()

# ==========================================
# 2. 메뉴 렌더링
# ==========================================
st.sidebar.markdown(f"**👤 접속자: {st.session_state['user_name']}**")
menu_selection = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu_selection == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu_selection == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu_selection == "📊 장비가동데이터":
    EquipmentDataTab(db_equipment).render()
elif menu_selection == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
