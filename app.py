import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

# CSS 에러 수정 및 스타일 적용
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
    </style>
    """, unsafe_allow_html=True)

# 자바스크립트를 이용한 클립보드 복사 함수 정의
def copy_to_clipboard(text):
    copy_script = f"""
        <script>
        function copyToClipboard() {{
            const text = "{text.replace('\\', '\\\\')}";
            navigator.clipboard.writeText(text).then(function() {{
                alert('경로가 복사되었습니다! [윈도우+R] 창에 붙여넣으세요.\\n\\n' + text);
            }}, function(err) {{
                console.error('복사 실패: ', err);
            }});
        }}
        </script>
        <button onclick="copyToClipboard()" style="
            padding: 5px 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
            ">📎 첨부</button>
    """
    return copy_script

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
    side_col1, side_col2 = st.sidebar.columns([2, 1])
    with side_col1:
        st.markdown(f"👤 **{st.session_state['user_name']}**님")
    with side_col2:
        if st.button("로그아웃"):
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
                    "대상 선택", options=df.index, 
                    format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']} | {df.iloc[x]['작성자']} | {df.iloc[x]['업무내용'][:10]}..."
                )
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df.loc[edit_idx, "장비"]) if df.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"], height=200)
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
                    format_func=lambda x: f"[{df.iloc[x]['날짜']}] {df.iloc[x]['장비']} | {df.iloc[x]['작성자']} | {df.iloc[x]['업무내용'][:15]}..."
                )
                st.sidebar.warning(f"⚠️ 상세:\n\n{df.loc[del_idx, '업무내용']}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    save_to_github(df.drop(del_idx), sha, "Delete Log")
                    st.rerun()

        # --- 메인 화면: 커스텀 리스트로 복사 기능 구현 ---
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        with header_col2:
            csv_download = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_download, file_name="work_log.csv")

        search = st.text_input("🔍 검색어 입력", label_visibility="collapsed")
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        # --- 표 대신 커스텀 복사 버튼을 포함한 인터페이스 구성 ---
        # Streamlit 표 내부에는 버튼 삽입이 불가하므로, 상단에 배치하거나 리스트형으로 보여줌
        # 여기서는 표 하단에 '최신 내역 복사' 기능을 제공하거나 표를 대신하여 복사 버튼을 포함한 HTML 표를 렌더링함
        
        st.markdown("##### 📝 업무 내역 (경로 확인 시 '첨부' 버튼 클릭)")
        
        # HTML 기반의 커스텀 표 생성 (복사 버튼 포함)
        html_table = f"""
        <table style="width:100%; border-collapse: collapse; font-size: 13px;">
            <tr style="background-color: #333; color: white; text-align: left;">
                <th style="padding: 10px; border: 1px solid #444;">날짜</th>
                <th style="padding: 10px; border: 1px solid #444;">장비</th>
                <th style="padding: 10px; border: 1px solid #444;">작성자</th>
                <th style="padding: 10px; border: 1px solid #444;">업무내용</th>
                <th style="padding: 10px; border: 1px solid #444;">첨부</th>
            </tr>
        """
        
        for idx, row in display_df.head(20).iterrows(): # 성능을 위해 최근 20개만 우선 표시
            html_table += f"""
            <tr style="border-bottom: 1px solid #444;">
                <td style="padding: 8px; border: 1px solid #444;">{row['날짜']}</td>
                <td style="padding: 8px; border: 1px solid #444;">{row['장비']}</td>
                <td style="padding: 8px; border: 1px solid #444;">{row['작성자']}</td>
                <td style="padding: 8px; border: 1px solid #444;">{row['업무내용']}</td>
                <td style="padding: 8px; border: 1px solid #444;">{copy_to_clipboard(row['첨부'])}</td>
            </tr>
            """
        html_table += "</table>"
        
        components.html(html_table, height=600, scrolling=True)

    except Exception as e:
        st.error(f"오류 발생: {e}")
