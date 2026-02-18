import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 (간격 및 크기 최적화) ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 2rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        
        /* 사이드바 내부 여백 최소화 */
        [data-testid="stSidebar"] .block-container { padding-top: 0rem; padding-bottom: 0rem; }
        
        /* 입력 칸 사이의 간격(마진) 줄이기 */
        div[data-testid="stForm"] > div {
            gap: 0.5rem !important;
        }
        
        /* 사이드바 헤더 디자인 */
        .sidebar-header {
            display: flex;
            align-items: center;
            gap: 10px;
            padding-top: 10px;
        }
        .user-info {
            font-size: 0.85rem;
            color: #666;
        }

        /* [핵심] 업무 내용 입력창 높이 확대 */
        div[data-testid="stTextarea"] textarea {
            min-height: 450px !important;
        }
        
        /* 메인 대시보드 제목 스타일 */
        .main-title {
            font-size: 1.8rem;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 20px;
        }

        /* 표 내부 줄바꿈 스타일 */
        div[data-testid="stDataFrame"] td {
            white-space: pre-wrap !important;
            vertical-align: top !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GitHub 연결 설정 ---
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    FILE_PATH = st.secrets["FILE_PATH"]
except Exception as e:
    st.error(f"⚠️ 연결 설정 오류: {e}")
    st.stop()

# --- 3. 데이터 함수 ---
def get_github_data():
    try:
        file_content = repo.get_contents(FILE_PATH)
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        df = df.loc[:, ~df.columns.duplicated()]
        cols_order = ["날짜", "장비", "작성자", "업무내용", "비고"]
        for col in cols_order:
            if col not in df.columns: df[col] = ""
        return df[cols_order].fillna("").astype(str), file_content.sha
    except Exception:
        return pd.DataFrame(columns=["날짜", "장비", "작성자", "업무내용", "비고"]), None

def save_to_github(df, sha, message):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    content = csv_buffer.getvalue()
    if sha: repo.update_file(FILE_PATH, message, content, sha)
    else: repo.create_file(FILE_PATH, "Initial Creation", content)

EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# --- 4. 세션 및 메인 로직 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login_form"):
        name = st.text_input("성함을 입력하세요")
        if st.form_submit_button("입장하기"):
            if name:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = name
                st.rerun()
else:
    # --- 사이드바 최상단 정보 ---
    side_col1, side_col2 = st.sidebar.columns([2, 1])
    with side_col1:
        st.markdown(f"<div class='user-info'>👤 {st.session_state['user_name']}님</div>", unsafe_allow_html=True)
    with side_col2:
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.sidebar.markdown("<div style='margin-top: -15px;'><hr></div>", unsafe_allow_html=True)

    try:
        df, sha = get_github_data()

        # [개선] 타이틀 여백 줄이기
        st.sidebar.subheader("📅 Daily 일지")
        mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"], label_visibility="collapsed")

        if mode == "➕ 작성":
            with st.sidebar.form("add_form", clear_on_submit=True):
                # 간격을 줄이기 위해 라벨을 위로 붙임
                d_val = st.date_input("날짜", datetime.today())
                e_type = st.selectbox("장비", EQUIPMENT_OPTIONS)
                # 업무 내용 칸을 크게 확대
                c_val = st.text_area("업무 내용")
                n_val = st.text_input("비고")
                
                if st.form_submit_button("저장하기", use_container_width=True):
                    if c_val:
                        new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val}])
                        save_to_github(pd.concat([df, new_row], ignore_index=True), sha, f"Add: {d_val}")
                        st.rerun()

        elif mode == "✏️ 수정":
            if not df.empty:
                edit_idx = st.sidebar.selectbox("대상 선택", options=df.index[::-1], format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']}", label_visibility="collapsed")
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df.loc[edit_idx, "장비"]) if df.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=df.loc[edit_idx, "비고"])
                    if st.form_submit_button("수정 완료", use_container_width=True):
                        df.loc[edit_idx, ["날짜", "장비", "업무내용", "비고"]] = [str(e_date), e_etype, e_content, e_note]
                        save_to_github(df, sha, f"Edit: {e_date}")
                        st.rerun()

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox("삭제 선택", options=df.index[::-1], format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']}", label_visibility="collapsed")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    save_to_github(df.drop(del_idx), sha, "Delete Log")
                    st.rerun()

        # --- 메인 화면 ---
        st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        search = st.text_input("🔍 검색어 입력", label_visibility="collapsed")
        
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        st.dataframe(
            display_df.iloc[::-1],
            use_container_width=True,
            column_config={
                "날짜": st.column_config.TextColumn("📅 날짜", width="small"),
                "장비": st.column_config.TextColumn("🔧 장비", width="small"),
                "작성자": st.column_config.TextColumn("👤 작성자", width="small"),
                "업무내용": st.column_config.TextColumn("📝 업무내용", width="large"),
                "비고": st.column_config.TextColumn("💡 비고", width="medium"),
            },
            hide_index=False
        )
        st.download_button(label="📥 엑셀 다운로드", data=display_df.iloc[::-1].to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig'), file_name="work_log.csv", mime="text/csv")

    except Exception as e:
        st.error(f"오류: {e}")
