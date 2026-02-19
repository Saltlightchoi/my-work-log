import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

# CSS 레이아웃 최적화: 여백 및 폰트 크기 조정
st.markdown("""
    <style>
        /* 메인 상단 여백 제거 및 패딩 축소 */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        
        /* 사이드바 너비 고정 및 상단 여백 제거 */
        [data-testid="stSidebar"] { width: 400px !important; }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.3rem !important; padding-top: 1rem !important; }
        
        /* 사이드바 로그인 정보 폰트 크기 최소화 */
        .sidebar-user-text { font-size: 11px !important; color: #aaaaaa; }

        /* 메인 타이틀 크기 축소 및 줄바꿈 방지 */
        .main-title { 
            font-size: 1.4rem !important; 
            font-weight: bold; 
            margin: 0 !important;
            padding: 0 !important;
            white-space: nowrap;
        }

        /* 엑셀 다운로드 버튼 크기 축소 */
        div.stDownloadButton > button {
            padding: 2px 10px !important;
            font-size: 11px !important;
            height: auto !important;
            min-height: 25px !important;
        }

        /* 안내 가이드 박스 디자인 */
        .info-box {
            background-color: #1e212b;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# 공통 경로 설정
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
    # --- 사이드바 상단 개선 (이름과 버튼 한 줄 배치) ---
    side_head1, side_head2 = st.sidebar.columns([2, 1])
    with side_head1:
        st.markdown(f"<p class='sidebar-user-text'>👤 {st.session_state['user_name']} 로그인 중</p>", unsafe_allow_html=True)
    with side_head2:
        if st.button("로그아웃", use_container_width=True):
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
                c_val = st.text_area("업무 내용", height=150)
                n_val = st.text_input("비고")
                f_name = st.text_input("파일명 (미입력 시 비워둠)")
                
                if st.form_submit_button("저장하기", use_container_width=True):
                    if c_val:
                        # 파일명이 비어 있으면 경로를 아예 비워둠 (요청 사항 반영)
                        full_path = BASE_PATH_RAW + f_name if f_name.strip() else ""
                        new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_path}])
                        save_to_github(pd.concat([df, new_row], ignore_index=True), sha, f"Add: {d_val}")
                        st.rerun()

        elif mode == "✏️ 수정":
            if not df.empty:
                edit_idx = st.sidebar.selectbox(
                    "대상 선택", options=df.index, 
                    format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']} | {df.iloc[x]['작성자']}"
                )
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df.loc[edit_idx, "장비"]) if df.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"], height=150)
                    e_note = st.text_input("비고 수정", value=df.loc[edit_idx, "비고"])
                    e_link = st.text_input("첨부 수정", value=df.loc[edit_idx, "첨부"])
                    if st.form_submit_button("수정 완료"):
                        df.loc[edit_idx, ["날짜", "장비", "업무내용", "비고", "첨부"]] = [str(e_date), e_etype, e_content, e_note, e_link]
                        save_to_github(df, sha, f"Edit: {e_date}")
                        st.rerun()

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox(
                    "삭제 선택", options=df.index,
                    format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']} | {df.iloc[x]['작성자']}"
                )
                st.sidebar.warning(f"⚠️ 삭제 대상 상세:\n\n{df.loc[del_idx, '업무내용']}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    save_to_github(df.drop(del_idx), sha, "Delete Log")
                    st.rerun()

        # --- 메인 화면 레이아웃 (잘림 방지) ---
        title_col, btn_col = st.columns([4, 1])
        with title_col:
            st.markdown("<p class='main-title'>📊 팀 업무일지 대시보드</p>", unsafe_allow_html=True)
        with btn_col:
            csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%m%d')}.csv")

        search = st.text_input("🔍 검색어 입력", label_visibility="collapsed")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        st.markdown("""
            <div class='info-box'>
                <p style='margin:0; font-size:0.85rem;'>📎 <b>사진 확인 가이드:</b> '첨부' 경로 클릭 후 <b>Ctrl+C</b> → <b>[윈도우+R]</b> 창에 붙여넣으세요.</p>
            </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            display_df,
            use_container_width=True,
