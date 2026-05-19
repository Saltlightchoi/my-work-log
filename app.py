import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
# ★ 잃어버린 로그인 로직 복구 ★
# ==========================================
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

if st.session_state['user_name'] is None:
    st.markdown("<h2 style='text-align: center;'>🔐 장비 관리 통합 시스템 로그인</h2>", unsafe_allow_html=True)
    with st.form("login_form"):
        user_input = st.text_input("👤 사용자 이름 (작성자 명을 입력하세요)")
        submit = st.form_submit_button("로그인", use_container_width=True)
        if submit and user_input.strip():
            st.session_state['user_name'] = user_input.strip()
            st.rerun()
    st.stop() # 로그인이 완료될 때까지 아래 코드는 실행되지 않습니다.

# ==========================================
# 2. 메뉴 렌더링 (로그인 성공 시 표시됨)
# ==========================================
st.sidebar.markdown(f"**👤 현재 접속자: {st.session_state['user_name']}**")
menu_selection = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu_selection == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu_selection == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu_selection == "📊 장비가동데이터":
    EquipmentDataTab(db_equipment).render()
elif menu_selection == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
