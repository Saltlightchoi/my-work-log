import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="GitHub 업무일지 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; }
        /* 표 내부의 줄바꿈 및 가독성 스타일 */
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

# --- 3. 데이터 읽기/쓰기 함수 ---
def get_github_data():
    try:
        file_content = repo.get_contents(FILE_PATH)
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        # 신규 항목 '장비종류'가 기존 파일에 없을 경우를 대비해 자동 추가
        if "장비" not in df.columns:
            df["장비"] = ""
        return df.fillna("").astype(str), file_content.sha
    except:
        # 파일이 아예 없을 경우 초기 생성 틀
        df = pd.DataFrame(columns=["날짜", "작성자", "장비", "업무내용", "비고"])
        return df, None

def save_to_github(df, sha, message):
    csv_buffer = io.StringIO()
    # 저장 시에는 항상 원본 순서대로 저장
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    content = csv_buffer.getvalue()
    if sha:
        repo.update_file(FILE_PATH, message, content, sha)
    else:
        repo.create_file(FILE_PATH, "Initial Log Creation", content)

# --- 4. 드롭다운 옵션 설정 ---
EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# --- 5. 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login_form"):
        input_name = st.text_input("성함을 입력하고 입장하세요")
        if st.form_submit_button("입장하기"):
            if input_name:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = input_name
                st.rerun()
            else:
                st.error("성함을 입력해주세요.")
else:
    st.sidebar.title(f"👋 {st.session_state['user_name']}님")
    if st.sidebar.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        # 데이터 로드
        df, sha = get_github_data()

        st.sidebar.title("📅 Daily 일지")
        mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add_form"):
                d_val = st.date_input("날짜", datetime.today())
                e_type = st.selectbox("장비", EQUIPMENT_OPTIONS) # 드롭다운 추가
                c_val = st.text_area("업무 내용 (Shift+Enter로 줄바꿈)")
                n_val = st.text_input("비고")
                
                if st.form_submit_button("저장하기"):
                    if c_val:
                        new_row = pd.DataFrame([{
                            "날짜": str(d_val), 
                            "작성자": st.session_state['user_name'], 
                            "장비종류": e_type,
                            "업무내용": c_val, 
                            "비고": n_val
                        }])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        save_to_github(updated_df, sha, f"Add: {d_val}")
                        st.success("저장되었습니다!")
                        st.rerun()

        elif mode == "✏️ 수정":
            if not df.empty:
                # 수정 시에는 최신순으로 보여줌
                display_options = df.index[::-1]
                edit_idx = st.sidebar.selectbox("수정 대상 선택", options=display_options, 
                                              format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비종류']} | {df.iloc[x]['업무내용'][:10]}...")
                with st.sidebar.form("edit_form"):
                    e_date = st.date_input("날짜 수정", value=pd.to_datetime(df.loc[edit_idx, "날짜"]))
                    # 기존 값이 옵션에 없으면 '기타'로 기본값 설정
                    current_etype = df.loc[edit_idx, "장비종류"]
                    etype_idx = EQUIPMENT_OPTIONS.index(current_etype) if current_etype in EQUIPMENT_OPTIONS else 0
                    e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=etype_idx)
                    
                    e_content = st.text_area("내용 수정", value=df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=df.loc[edit_idx, "비고"])
                    
                    if st.form_submit_button("수정 완료"):
                        df.loc[edit_idx, ["날짜", "장비", "업무내용", "비고"]] = [str(e_date), e_etype, e_content, e_note]
                        save_to_github(df, sha, f"Edit: {e_date}")
                        st.rerun()

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox("삭제 대상", options=df.index[::-1], format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['장비']}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    updated_df = df.drop(del_idx)
                    save_to_github(updated_df, sha, "Delete Log")
                    st.rerun()

        # --- 메인 대시보드 출력 ---
        st.title("📊 팀 업무일지 대시보드")
        search = st.text_input("🔍 검색어 입력 (장비, 이름, 내용 등)")
        
        # 필터링 적용
        display_df = df.copy()
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        # [요청사항] 최신 기록이 맨 위로 오도록 역순 정렬
        display_df = display_df.iloc[::-1]

        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "날짜": st.column_config.TextColumn("📅 날짜", width="small"),
                "작성자": st.column_config.TextColumn("👤 작성자", width="small"),
                "장비종류": st.column_config.TextColumn("🔧 장비", width="small"),
                "업무내용": st.column_config.TextColumn("📝 업무내용", width="large"),
                "비고": st.column_config.TextColumn("💡 비고", width="medium"),
            },
            hide_index=False
        )

        # 엑셀 다운로드 (최신순으로 정렬된 상태로 다운로드)
        csv_download = display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 현재 목록 엑셀 다운로드", data=csv_download, file_name=f"work_log_{datetime.now().strftime('%m%d')}.csv", mime="text/csv")

    except Exception as e:
        st.error(f"데이터 오류: {e}")
