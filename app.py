import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem !important; }
        [data-testid="stSidebar"] { width: 420px !important; }
        .main-title { font-size: 1.8rem !important; font-weight: bold; line-height: 2.0; }
        
        /* 안내 문구 스타일 */
        .path-guide {
            font-size: 0.8rem;
            color: #ffaa00;
            background-color: #332200;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            line-height: 1.4;
        }
    </style>
    """, unsafe_allow_html=True)

# 공통 경로 설정 (윈도우 경로를 웹 링크 가능 형태로 변환하기 위한 베이스)
# 브라우저에서 열기 위해서는 file:// 형식이 필요합니다.
BASE_PATH_DISPLAY = r"\\192.168.0.100\500 생산\550 국내CS\공유사진"
BASE_PATH_LINK = "file://192.168.0.100/500%20생산/550%20국내CS/공유사진/"

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
    # 사이드바 상단
    st.sidebar.markdown(f"👤 **{st.session_state['user_name']}**님 로그인 중")
    if st.sidebar.button("로그아웃"):
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
                c_val = st.text_area("업무 내용")
                n_val = st.text_input("비고")
                
                # 경로 안내 가이드
                st.markdown(f"""
                <div class='path-guide'>
                📂 <b>자동 경로 적용 중:</b><br>
                {BASE_PATH_DISPLAY}<br>
                위 폴더에 사진을 넣고 <b>파일명</b>만 아래에 입력하세요.
                </div>
                """, unsafe_allow_html=True)
                
                f_name = st.text_input("파일명 (예: 사진1.jpg / 미입력 시 폴더연결)")
                
                if st.form_submit_button("저장하기", use_container_width=True):
                    if c_val:
                        # 파일명을 입력하면 풀경로, 안하면 폴더경로 저장
                        full_link = BASE_PATH_LINK + f_name if f_name else BASE_PATH_LINK
                        new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_link}])
                        save_to_github(pd.concat([df, new_row], ignore_index=True), sha, f"Add: {d_val}")
                        st.rerun()

        elif mode == "✏️ 수정":
            if not df.empty:
                edit_idx = st.sidebar.selectbox("대상 선택", options=df.index, format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']}")
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df.loc[edit_idx, "장비"]) if df.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=df.loc[edit_idx, "비고"])
                    e_link = st.text_input("첨부 경로 수정(전체URL)", value=df.loc[edit_idx, "첨부"])
                    if st.form_submit_button("수정 완료"):
                        df.loc[edit_idx, ["날짜", "장비", "업무내용", "비고", "첨부"]] = [str(e_date), e_etype, e_content, e_note, e_link]
                        save_to_github(df, sha, f"Edit: {e_date}")
                        st.rerun()

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox("삭제 선택", options=df.index, format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']}")
                if st.sidebar.button("🗑️ 최종 삭제"):
                    save_to_github(df.drop(del_idx), sha, "Delete Log")
                    st.rerun()

        # 메인 화면
        header_col1, header_col2 = st.columns([5, 1])
        with header_col1:
            st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        with header_col2:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            csv_download = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_download, file_name="work_log.csv", mime="text/csv")

        search = st.text_input("🔍 검색어 입력", label_visibility="collapsed")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "날짜": st.column_config.TextColumn("📅 날짜"),
                "장비": st.column_config.TextColumn("🔧 장비"),
                "작성자": st.column_config.TextColumn("👤 작성자"),
                "업무내용": st.column_config.TextColumn("📝 업무내용", width="large"),
                "비고": st.column_config.TextColumn("💡 비고"),
                "첨부": st.column_config.LinkColumn("📎 사진보기", placeholder="확인하기"),
            },
            hide_index=False
        )

    except Exception as e:
        st.error(f"오류: {e}")
