import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        [data-testid="stSidebar"] { width: 420px !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        
        .main-title { 
            font-size: 1.6rem !important; 
            font-weight: bold; 
            margin-top: -10px;
            margin-bottom: 5px;
            white-space: nowrap;
        }

        div.stDownloadButton > button {
            width: 100% !important;
            height: auto !important;
            padding: 5px !important;
            font-size: 12px !important;
        }

        .path-guide {
            font-size: 0.8rem;
            color: #ffaa00;
            background-color: #332200;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        [data-testid="stSidebar"] { width: 420px !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        
        .main-title { 
            font-size: 1.6rem !important; 
            font-weight: bold; 
            margin-top: -10px;
            margin-bottom: 5px;
            white-space: nowrap;
        }

        div.stDownloadButton > button {
            width: 100% !important;
            height: auto !important;
            padding: 5px !important;
            font-size: 12px !important;
        }

        .path-guide {
            font-size: 0.8rem;
            color: #ffaa00;
            background-color: #332200;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            line-height: 1.4;
        }

        /* 복사 버튼을 위한 커스텀 스타일 */
        .copy-btn {
            background-color: #4CAF50;
            color: white;
            padding: 2px 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

BASE_PATH_DISPLAY = r"\\192.168.0.100\500 생산\550 국내CS\공유사진"
BASE_PATH_RAW = r"\\192.168.0.100\500 생산\550 국내CS\공유사진\\"

# --- 2. GitHub 연결 설정 ---
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    FILE_PATH = st.secrets["FILE_PATH"]
except Exception as e:
    st.error(f"⚠️ 연결 설정 오류: {e}")
    st.stop()

# --- 3. 데이터 로직 ---
def get_github_data():
    try:
        file_content = repo.get_contents(FILE_PATH)
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        df = df.loc[:, ~df.columns.duplicated()]
        cols_order = ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"]
        for col in cols_order:
            if col not in df.columns: df[col] = ""
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date.astype(str)
        df = df.sort_values(by='날짜', ascending=False).reset_index(drop=True)
        return df[cols_order].fillna("").astype(str), file_content.sha
    except Exception:
        return pd.DataFrame(columns=["날짜", "장비", "작성자", "업무내용", "비고", "첨부"]), None

def save_to_github(df, sha, message):
    csv_buffer = io.StringIO()
    df = df.sort_values(by='날짜', ascending=False)
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    content = csv_buffer.getvalue()
    if sha: repo.update_file(FILE_PATH, message, content, sha)
    else: repo.create_file(FILE_PATH, "Initial Creation", content)

EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# --- 4. 메인 로직 ---
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
    side_col1, side_col2 = st.sidebar.columns([2, 1])
    with side_col1:
        st.markdown(f"👤 **{st.session_state['user_name']}**님")
    with side_col2:
        if st.button("로그아웃", key="logout_btn"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.sidebar.divider()

    try:
        df, sha = get_github_data()
        mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add_form", clear_on_submit=True):
                d_val = st.date_input("날짜", datetime.today())
                e_type = st.selectbox("장비", EQUIPMENT_OPTIONS)
                c_val = st.text_area("업무 내용", height=250)
                n_val = st.text_input("비고")
                st.markdown(f"<div class='path-guide'>📂 <b>자동 경로:</b> {BASE_PATH_DISPLAY}</div>", unsafe_allow_html=True)
                f_name = st.text_input("파일명 (예: 사진1.jpg)")
                
                if st.form_submit_button("저장하기", use_container_width=True):
                    if c_val:
                        full_path = BASE_PATH_RAW + f_name if f_name else BASE_PATH_RAW
                        new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_path}])
                        save_to_github(pd.concat([df, new_row], ignore_index=True), sha, f"Add: {d_val}")
                        st.rerun()

        elif mode == "✏️ 수정":
            if not df.empty:
                edit_idx = st.sidebar.selectbox(
                    "대상 선택", 
                    options=df.index, 
                    format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']} | {df.iloc[x]['작성자']} | {df.iloc[x]['업무내용'][:10]}..."
                )
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df.loc[edit_idx, "장비"]) if df.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"], height=200)
                    e_note = st.text_input("비고 수정", value=df.loc[edit_idx, "비고"])
                    e_link = st.text_input("첨부 경로 수정", value=df.loc[edit_idx, "첨부"])
                    if st.form_submit_button("수정 완료"):
                        df.loc[edit_idx, ["날짜", "장비", "업무내용", "비고", "첨부"]] = [str(e_date), e_etype, e_content, e_note, e_link]
                        save_to_github(df, sha, f"Edit: {e_date}")
                        st.rerun()

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox(
                    "삭제 선택", 
                    options=df.index, 
                    format_func=lambda x: f"[{df.iloc[x]['날짜']}] {df.iloc[x]['장비']} | {df.iloc[x]['작성자']} | {df.iloc[x]['업무내용'][:15]}..."
                )
                st.sidebar.warning(f"⚠️ 선택 상세:\n\n{df.loc[del_idx, '업무내용']}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    save_to_github(df.drop(del_idx), sha, "Delete Log")
                    st.rerun()

        # --- 메인 화면 ---
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        with header_col2:
            csv_download = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_download, file_name="work_log.csv", mime="text/csv")

        search = st.text_input("🔍 검색어 입력", label_visibility="collapsed")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        # --- 첨부파일 클릭 자동 복사 구현 ---
        # 1. 텍스트 열로 보여주되, Streamlit의 기본 기능을 활용하여 마우스 오버 시 우측의 복사 버튼이 뜨게 함
        # 2. '첨부' 글자만 남기고 실제 경로는 help 툴팁에 넣어 깔끔하게 만듦
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "날짜": st.column_config.TextColumn("📅 날짜"),
                "장비": st.column_config.TextColumn("🔧 장비"),
                "작성자": st.column_config.TextColumn("👤 작성자"),
                "업무내용": st.column_config.TextColumn("📝 업무내용", width="large"),
                "비고": st.column_config.TextColumn("💡 비고"),
                "첨부": st.column_config.TextColumn(
                    "📎 첨부(클릭시 복사)", 
                    help="셀을 클릭한 후 우측에 나타나는 복사 아이콘을 누르거나, Ctrl+C를 누르세요. 그 후 [윈도우+R] 창에 붙여넣으시면 됩니다."
                )
            },
            hide_index=True
        )
        
        st.info("💡 **사진 확인 방법**: '첨부' 칸의 경로를 클릭 후 복사(Ctrl+C)하여 [윈도우 키 + R] 창에 붙여넣으세요.")

    except Exception as e:
        st.error(f"오류 발생: {e}")
