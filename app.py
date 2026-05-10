import streamlit as st
from github import Github

# ==========================================
# ★ 모듈(클래스) 수입 (에러 방지용 완벽 연결)
# ==========================================
try:
    from config import DataManager
    from tab_work_log import WorkLogTab
    from tab_cs_check import CSCheckSheetTab
    from tab_equipment_data import EquipmentDataTab
    from tab_ecn_stn import ECNSTNTab
except ModuleNotFoundError as e:
    st.error(f"🚨 **모듈 로드 실패:** `{e.name}.py` 파일을 찾을 수 없습니다.")
    st.info("app.py와 같은 폴더 안에 5개의 탭 파일들이 모두 정상적으로 저장되어 있는지 확인해주세요.")
    st.stop()

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
        
        /* 대시보드 카드 디자인 */
        .dash-card {
            background-color: #ffffff; border-radius: 10px; padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #4CAF50;
            margin-bottom: 15px;
        }
        .dash-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }
        .dash-stat { font-size: 24px; font-weight: bold; color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 메인 실행 (관제탑)
# ==========================================
def main():
    try:
        gh_token = st.secrets["GITHUB_TOKEN"]
        repo_name = st.secrets["REPO_NAME"]
        file_path = st.secrets["FILE_PATH"]
    except FileNotFoundError:
        st.error("🚨 **치명적 오류: `.streamlit/secrets.toml` 파일을 찾을 수 없습니다!**")
        st.stop()
    except KeyError as e:
        st.error(f"🚨 **치명적 오류: secrets.toml 파일 안에 {e} 설정이 빠져 있습니다!**")
        st.stop()

    try:
        g = Github(gh_token)
        repo = g.get_repo(repo_name)
        db_log = DataManager(repo, file_path, ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 깃허브 저장소 접근 오류 (권한 또는 저장소 이름 확인 필요): {e}")
        st.stop()

    if 'logged_in' not in st.session_state: 
        st.session_state.update({'logged_in': False, 'user_name': ""})

    if not st.session_state['logged_in']:
        with st.form("login"):
            name = st.text_input("성함")
            if st.form_submit_button("입장") and name: 
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        st.markdown("<h4 style='margin-bottom: 5px; color: #1f2937;'>📂 대시보드 메뉴 이동</h4>", unsafe_allow_html=True)
        
        menu_col, logout_col, empty_col = st.columns([3.5, 1, 5.5])
        
        with menu_col:
            # ★ 핵심 해결 코드: 내부 라벨을 바꿔서 에러 강제 초기화!
            menu_selection = st.selectbox(
                "새로운_메뉴_인식표", 
                ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"],
                label_visibility="collapsed"
            )
            
        with logout_col:
            if st.button("🚪 로그아웃", use_container_width=True): 
                st.session_state['logged_in'] = False
                st.rerun()

        st.sidebar.markdown(f"👤 **{st.session_state['user_name']}** 님 환영합니다.")

        # 모듈 렌더링
        if menu_selection == "📝 업무일지": 
            WorkLogTab(db_log).render()
        elif menu_selection == "✅ 장비 제작 Flow": 
            CSCheckSheetTab(db_flow).render()
        elif menu_selection == "📊 장비가동데이터": 
            EquipmentDataTab(repo).render()
        elif menu_selection == "🛠️ ECN & STN": 
            ECNSTNTab(repo).render()

if __name__ == "__main__": 
    main()
