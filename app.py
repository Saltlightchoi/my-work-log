import streamlit as st
from github import Github
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 0. 구글 시트 및 깃허브 연결 (★ 캐싱 적용)
# ==========================================
@st.cache_resource 
def init_connections(): 
    # 1. 구글 시트 ID 세팅
    SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"  # 기존 마스터 파일
    JAM_SPREADSHEET_ID = "여기에_새로_만든_Jam이력_파일_ID_입력"     # 새로 만든 Jam 파일
    
    # 2. 구글 시트 연결 (4개)
    db1 = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"]) 
    db2 = DataManager(SPREADSHEET_ID, "CS체크리스트") 
    db3 = DataManager(SPREADSHEET_ID, "ECN_STN")
    db_jam = DataManager(JAM_SPREADSHEET_ID, "SLH1 #1")
    
    # 3. ★ 장비가동데이터용 깃허브 연결 (대표님 원본 코드 완벽 복구) ★
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
        else:
            g = Github()
        repo = g.get_repo("saltlightchoi/my-work-log") 
    except Exception:
        repo = None
    
    # 5개의 연결 객체를 순서대로 반환합니다.
    return db1, db2, db3, db_jam, repo

# 5개의 변수로 정확히 받아줍니다.
db_work_log, db_cs_check, db_ecn, db_jam_log, repo = init_connections()
# ==========================================
# 1. 환경 설정 및 타이틀 드롭다운 마법(CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

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
            min-height: 65px !important;
        }
        
        /* 글자 크기, 굵기, 줄간격 설정 및 잘림 방지 */
        section[data-testid="stMain"] div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] {
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            line-height: 1.5 !important;
            overflow: visible !important;
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
# 사이드바 렌더링 부분에서 깔끔하게 db_jam_log만 넘겨주면 됩니다!
elif menu == "🚨 Jam & 트러블슈팅 이력": 
    from tab_jam_log import JamLogTab
    tab = JamLogTab(db_jam_log) # 에러 마스터는 이 안에서 알아서 찾아옵니다.
    tab.render()
