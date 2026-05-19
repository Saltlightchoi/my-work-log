import streamlit as st
from github import Github
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 0-1. 구글 시트 설정 (업무일지, CS체크, ECN 용)
# ==========================================
SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"
db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

# ==========================================
# 0-2. 깃허브 설정 (장비가동데이터 엑셀 파일 용)
# ==========================================
try:
    if "GITHUB_TOKEN" in st.secrets:
        g = Github(st.secrets["GITHUB_TOKEN"])
    else:
        g = Github()
    # ★ 올려주신 에러 스크린샷 경로를 참고하여 작성했습니다.
    # 만약 저장소 이름이 다르다면 아래 문자열을 수정해 주세요!
    repo = g.get_repo("saltlightchoi/my-work-log") 
except Exception as e:
    repo = None

# ==========================================
# 1. 환경 설정 및 로그인 로직
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 350px !important; }
        .main-title { font-size: 2rem !important; font-weight: bold; padding-bottom: 15px !important; }
    </style>
""", unsafe_allow_html=True)

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
menu = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu == "📝 업무일지":
    WorkLogTab(db_work_log).render()
elif menu == "✅ 장비 제작 Flow":
    CSCheckSheetTab(db_cs_check).render()
elif menu == "📊 장비가동데이터":
    if repo:
        # 기존 방식 그대로 repo를 넘겨줍니다.
        EquipmentDataTab(repo).render()
    else:
        st.error("깃허브 저장소를 불러오지 못했습니다. app.py의 저장소 이름을 확인해 주세요.")
elif menu == "🛠️ ECN & STN":
    ECNSTNTab(db_ecn).render()
