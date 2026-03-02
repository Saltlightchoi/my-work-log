import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# ==========================================
# 1. 환경 설정 및 기본 상수 (Constants)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] { padding: 2px 5px !important; font-size: 12px !important; height: 28px !important; }
        .main-title { font-size: 1.5rem !important; font-weight: bold; margin: 0 !important; padding-bottom: 10px !important; }
        div.stDownloadButton > button { padding: 4px 10px !important; font-size: 12px !important; width: 100% !important; }
        .info-box { background-color: #1e212b; padding: 12px; border-radius: 4px; border-left: 3px solid #4CAF50; margin-bottom: 15px; font-size: 13px; }
        .streamlit-expanderHeader { font-weight: bold !important; font-size: 1.1rem !important; color: #4CAF50 !important; }
    </style>
    """, unsafe_allow_html=True)

BASE_PATH_RAW = r"\\192.168.0.100\500 생산\550 국내CS\공유사진\\"
EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# 35가지 CS 템플릿 항목 (코드 길이 축소를 위해 일부 생략 표기했으나, 실제론 기존 35개 모두 넣으시면 됩니다)
CS_TEMPLATE = [
    {"대항목": "공통", "순서": 1, "작업내용": "I/O Check\n- Out Put으로 동작 후 In Put LED 확인...", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    # ... (기존 35개 리스트 그대로 복붙 유지) ...
]


# ==========================================
# 2. 데이터 관리 공장 (Class Definition)
# ==========================================
class DataManager:
    """GitHub CSV 파일을 불러오고 저장하는 전용 클래스"""
    def __init__(self, repo, file_path, text_columns):
        self.repo = repo
        self.file_path = file_path
        self.text_columns = text_columns # 강제로 문자로 인식할 컬럼들

    def load(self):
        try:
            file_content = self.repo.get_contents(self.file_path)
            df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
            df = df.loc[:, ~df.columns.duplicated()]
            # 빈칸 에러(Float 인식) 방지 로직
            for col in self.text_columns:
                if col not in df.columns: df[col] = ""
                else: df[col] = df[col].fillna("").astype(str)
            return df, file_content.sha
        except:
            return pd.DataFrame(columns=self.text_columns), None

    def save(self, df, sha, message):
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        if sha: self.repo.update_file(self.file_path, message, csv_buffer.getvalue(), sha)
        else: self.repo.create_file(self.file_path, "Init Creation", csv_buffer.getvalue())


# ==========================================
# 3. 화면 UI 보따리 (Functions)
# ==========================================
def render_work_log_page(db_log):
    """팀 업무일지 화면을 그려주는 함수"""
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
    
    if mode == "➕ 작성":
        with st.sidebar.form("add_form", clear_on_submit=True):
            d_val = st.date_input("날짜", datetime.today())
            e_type = st.selectbox("장비", EQUIPMENT_OPTIONS)
            c_val = st.text_area("업무 내용", height=120)
            n_val = st.text_input("비고")
            f_name = st.text_input("파일명 (미입력 시 비워둠)")
            if st.form_submit_button("저장하기", use_container_width=True):
                if c_val:
                    full_path = BASE_PATH_RAW + f_name if f_name.strip() else ""
                    new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_path}])
                    db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d_val}")
                    st.rerun()
                    
    # ... (수정/삭제 로직 기존과 동일하게 유지 - 분량상 생략) ...

    # 대시보드 출력부
    head_c1, head_c2 = st.columns([5, 1])
    with head_c1: st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    with head_c2:
        csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 엑셀", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv")

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    search = st.text_input("🔍 검색", label_visibility="collapsed", placeholder="검색어를 입력하세요...")
    display_df = df_log.copy()
    if search: display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("📝 업무내용", width="large"), "첨부": st.column_config.TextColumn("📎 첨부(클릭복사)")})


def render_cs_flow_page(db_flow):
    """장비제작 Flow 화면을 그려주는 함수"""
    df_flow, sha_flow = db_flow.load()
    st.markdown("<div class='main-title'>⚙️ CS 작업 체크 시트 (대항목 관리)</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("➕ 새 프로젝트(호기) 시작하기"):
            with st.form("new_proj_form"):
                new_proj = st.text_input("새 프로젝트명 (예: SLH1 #6호기)")
                if st.form_submit_button("템플릿으로 생성") and new_proj and new_proj not in project_list:
                    new_df = pd.DataFrame(CS_TEMPLATE)
                    new_df["프로젝트명"] = new_proj
                    new_df["업데이트일"] = ""
                    new_df['group_id'] = (new_df['대항목'] != new_df['대항목'].shift()).cumsum()
                    new_df["순서"] = new_df.groupby('group_id').cumcount() + 1
                    db_flow.save(pd.concat([df_flow, new_df.drop(columns=['group_id'])], ignore_index=True), sha_flow, f"Create: {new_proj}")
                    st.rerun()

    if project_list:
        sel_col, empty_col, save_col, del_col = st.columns([6, 2, 1, 1])
        with sel_col: selected_proj = st.selectbox("📌 진행 상황 확인할 프로젝트", project_list)
        with save_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_save = st.button("💾 저장", use_container_width=True)
        with del_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_del = st.button("🗑️ 삭제", use_container_width=True)

        mask = df_flow["프로젝트명"] == selected_proj
        proj_df = df_flow[mask].copy()
        
        # 편집기 UI 출력
        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        groups = proj_df.groupby('group_id')
        edited_dfs = []
        for group_id, group_df in groups:
            cat = group_df['대항목'].iloc[0]
            with st.expander(f"📍 대항목: {cat} 작업 리스트", expanded=False):
                edited_cat_df = st.data_editor(
                    group_df.drop(columns=['group_id']).reset_index(drop=True),
                    use_container_width=True, hide_index=True, num_rows="dynamic",
                    key=f"editor_{selected_proj}_{group_id}",
                    column_config={"프로젝트명": None, "대항목": None, "순서": st.column_config.NumberColumn("No", disabled=True, width="small")}
                )
                edited_cat_df["대항목"] = cat
                edited_cat_df["프로젝트명"] = selected_proj
                edited_dfs.append(edited_cat_df)

        # 저장 로직
        if btn_save:
            updated_proj_df = pd.concat(edited_dfs, ignore_index=True)
            if not updated_proj_df.empty:
                updated_proj_df['group_id'] = (updated_proj_df['대항목'] != updated_proj_df['대항목'].shift()).cumsum()
                updated_proj_df["순서"] = updated_proj_df.groupby('group_id').cumcount() + 1
                updated_proj_df["업데이트일"] = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"
                updated_proj_df = updated_proj_df.drop(columns=['group_id'])
            
            df_flow = pd.concat([df_flow[~mask], updated_proj_df], ignore_index=True)
            db_flow.save(df_flow, sha_flow, f"Update: {selected_proj}")
            st.rerun()

        # 삭제 로직
        if btn_del:
            db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
            st.rerun()
    else:
        st.info("진행 중인 프로젝트가 없습니다.")


# ==========================================
# 4. 메인 실행 (Main App) - 여기서 위 함수들을 조립합니다.
# ==========================================
def main():
    # 깃허브 연결 세팅
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        
        # 클래스를 이용해 2개의 데이터 공장을 찍어냅니다!
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 연결 설정 오류: {e}")
        return

    # 로그인 로직
    if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user_name': ""})
    
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            name = st.text_input("성함을 입력하세요")
            if st.form_submit_button("입장하기") and name:
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        # 사이드바
        st.sidebar.markdown(f"👤 {st.session_state['user_name']} 님")
        if st.sidebar.button("로그아웃"): 
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.sidebar.divider()
        page_menu = st.sidebar.radio("📌 메뉴 이동", ["📝 팀 업무일지", "⚙️ 장비제작 Flow"])
        
        # 메뉴에 따라 위에서 만든 보따리(함수)를 부르기만 하면 끝!
        if page_menu == "📝 팀 업무일지":
            render_work_log_page(db_log)
        elif page_menu == "⚙️ 장비제작 Flow":
            render_cs_flow_page(db_flow)

# 프로그램의 진짜 시작점
if __name__ == "__main__":
    main()
