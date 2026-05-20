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
# 1. 환경 설정 및 타이틀 드롭다운 마법(CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

# ★ 잘림 현상을 해결한 핵심 CSS 영역입니다.
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 3rem !important; padding-bottom: 2rem !important; }
        
        /* 드롭다운 박스의 높이를 강제로 늘려서 글자가 숨막히지 않게 여백을 줍니다 */
        section[data-testid="stMain"] div[data-testid="stSelectbox"]:first-of-type > div[data-baseweb="select"] > div {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            cursor: pointer !important;
            height: auto !important; 
            min-height: 65px !important; /* 높이 확보 */
        }
        
        /* 글자 크기, 굵기, 줄간격 설정 및 잘림 방지(overflow) */
        section[data-testid="stMain"] div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] {
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            line-height: 1.5 !important;
            overflow: visible !important; /* 상자를 벗어나도 글씨가 온전히 보이게 강제 설정 */
        }
        
        /* 우측 화살표 아이콘 크기 및 위치 조정 */
        section[data-testid="stMain"] div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] svg {
            width: 2rem !important;
            height: 2rem !important;
            color: #888 !important;
            margin-top: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 로그인 및 탭(메뉴) 상태 유지 로직
# ==========================================
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = None

if 'current_menu' not in st.session_state:
    st.session_state['current_menu'] = "📝 팀 업무일지 대시보드"

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
# 3. 사이드바 (접속자 고정) & 탭 렌더링
# ==========================================
st.sidebar.markdown(f"### 👤 {st.session_state['user_name']} 님")
st.sidebar.markdown("---")

menu = st.session_state['current_menu']

if menu == "📝 팀 업무일지 대시보드":
    WorkLogTab(db_work_log).render()
elif menu == "✅ 장비 제작 Flow 전체 현황판":
    CSCheckSheetTab(db_cs_check).render()
elif menu == "📊 장비가동데이터":
    if repo:
        EquipmentDataTab(repo).render()
    else:
        st.error("깃허브 저장소를 불러오지 못했습니다.")
elif menu == "🛠️ ECN & STN (장비 파트 및 수정사항 관리)":
    ECNSTNTab(db_ecn).render()
