import streamlit as st
from github import Github

# ==========================================
# ★ 모듈(클래스) 수입 (에러 방지용 완벽 연결)
# ==========================================
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

# ==========================================
# 1. 환경 설정 및 전체 디자인 (CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { max-width: 98% !important; padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 350px !important; }
        html, body, [class*="css"] { font-size: 16px !important; }
        .main-title { font-size: 2rem !important; font-weight: bold; padding-bottom: 15px !important; margin-top: -10px; }
        .info-box { background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 6px solid #4CAF50; margin-bottom: 15px; color: #333; font-size: 15px; }
        
        .final-report-table { width: 100%; border-collapse: collapse; border: 2px solid #000000 !important; font-size: 14px; color: #000000; background-color: #ffffff; }
        .final-report-table th, .final-report-table td { border: 1px solid #000000 !important; padding: 8px 10px; text-align: center; }
        .final-report-table th { background-color: #d9e1f2 !important; font-weight: bold; font-size: 15px; }
        .t-left { text-align: left !important; }
        div[data-testid="stSidebar"] button { width: 100% !important; font-weight: bold; font-size: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 메인 실행 (관제탑)
# ==========================================
def main():
    # 깃허브 및 DB 초기화
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 깃허브 연결 설정 오류: {e}")
        return

    # 로그인 세션 관리
    if 'logged_in' not in st.session_state: 
        st.session_state.update({'logged_in': False, 'user_name': ""})

    if not st.session_state['logged_in']:
        with st.form("login"):
            name = st.text_input("성함")
            if st.form_submit_button("입장") and name: 
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        # ★ 화면 상단 레이아웃 (글씨 짤림 차단 + 드롭다운 크기 절반 예쁘게 압축)
        st.markdown("<h4 style='margin-bottom: 5px; color: #1f2937;'>📂 대시보드 메뉴 이동</h4>", unsafe_allow_html=True)
        
        menu_col, logout_col, empty_col = st.columns([3.5, 1, 5.5])
        
        with menu_col:
            menu_selection = st.selectbox(
                "메뉴선택",
                ["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터", "🛠️ ECN & STN"],
                label_visibility="collapsed"
            )
            
        with logout_col:
            if st.button("🚪 로그아웃", use_container_width=True): 
                st.session_state['logged_in'] = False
                st.rerun()

        st.sidebar.markdown(f"👤 **{st.session_state['user_name']}** 님 환영합니다.")

        # ★ 선택된 메뉴에 따라 각 파일에 있는 클래스 모듈을 쏙쏙 뽑아와서 화면에 그려줍니다!
        if menu_selection == "📝 업무일지": 
            WorkLogTab(db_log).render()
        elif menu_selection == "✅ CS 작업체크시트": 
            CSCheckSheetTab(db_flow).render()
        elif menu_selection == "📊 장비가동데이터": 
            EquipmentDataTab(repo).render()
        elif menu_selection == "🛠️ ECN & STN": 
            ECNSTNTab(repo).render()

if __name__ == "__main__": 
    main()
