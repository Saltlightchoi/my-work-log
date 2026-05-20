import streamlit as st
from github import Github
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 0. 구글 시트 및 깃허브 설정
# ==========================================
SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"
db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

try:
    if "GITHUB_TOKEN" in st.secrets:
        g = Github(st.secrets["GITHUB_TOKEN"])
    else:
        g = Github()
    repo = g.get_repo("saltlightchoi/my-work-log") 
except Exception as e:
    repo = None

# ==========================================
# 1. 환경 설정 및 여백 정상화
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 3.5rem !important; padding-bottom: 2rem !important; }
        .main-title { font-size: 2rem !important; font-weight: bold; margin-bottom: 0px !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 로그인 로직
# ==========================================
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
# 3. 사이드바 (접속자 텍스트 고정) 및 전역 메뉴 상태
# ==========================================
st.sidebar.markdown(f"<div style='font-size: 16px; font-weight: bold; margin-bottom: 20px;'>👤 접속자: {st.session_state['user_name']}</div>", unsafe_allow_html=True)

# 메뉴 상태를 세션에 저장하여 각 탭에서도 공유할 수 있게 만듭니다.
if 'current_menu' not in st.session_state:
    st.session_state['current_menu'] = "📝 업무일지"

menu = st.session_state['current_menu']

# ==========================================
# 4. 메뉴 렌더링
# ==========================================
if menu == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu == "📊 장비가동데이터":
    if repo:
        EquipmentDataTab(repo).render()
    else:
        st.error("깃허브 저장소를 불러오지 못했습니다.")
elif menu == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
