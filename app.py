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
    </style>
    """, unsafe_allow_html=True)

# --- 2. GitHub 연결 설정 (Secrets 필수) ---
try:
    # Secrets에 저장한 토큰과 저장소 정보를 가져옵니다.
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    FILE_PATH = st.secrets["FILE_PATH"]
except Exception as e:
    st.error(f"⚠️ 연결 설정 오류: Secrets를 확인하세요. ({e})")
    st.stop()

# --- 3. 데이터 읽기/쓰기 함수 ---
def get_github_data():
    try:
        # GitHub에서 파일 내용을 가져옵니다.
        file_content = repo.get_contents(FILE_PATH)
        # UTF-8-SIG는 한글 깨짐 방지를 위함입니다.
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        return df.fillna("").astype(str), file_content.sha
    except:
        # 파일이 없으면 헤더가 포함된 빈 데이터프레임을 반환합니다.
        df = pd.DataFrame(columns=["날짜", "작성자", "업무내용", "비고"])
        return df, None

def save_to_github(df, sha):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    content = csv_buffer.getvalue()
    
    if sha:
        # 기존 파일이 있으면 업데이트
        repo.update_file(FILE_PATH, f"Update Log: {datetime.now()}", content, sha)
    else:
        # 파일이 없으면 새로 생성
        repo.create_file(FILE_PATH, "Initial Log Creation", content)

# --- 4. 세션 관리 (로그인) ---
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
    # --- 5. 메인 시스템 화면 ---
    st.sidebar.title(f"👋 {st.session_state['user_name']}님")
    if st.sidebar.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        # GitHub에서 실시간 데이터 로드
        df, sha = get_github_data()

        st.sidebar.title("📅 Daily 일지")
        mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add_form"):
                d_val = st.date_input("날짜", datetime.today())
                c_val = st.sidebar.text_area("업무 내용")
                n_val = st.sidebar.text_input("비고")
                
                if st.form_submit_button("저장하기"):
                    if c_val:
                        # 데이터 추가 및 GitHub 전송
                        new_row = pd.DataFrame([{"날짜":str(d_val), "작성자":st.session_state['user_name'], "업무내용":c_val, "비고":n_val}])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        save_to_github(updated_df, sha)
                        st.success("GitHub에 안전하게 저장되었습니다!")
                        st.rerun()
                    else:
                        st.sidebar.error("내용을 입력해주세요.")

        elif mode == "❌ 삭제":
            if not df.empty:
                del_idx = st.sidebar.selectbox("삭제 대상", options=df.index,
                                             format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['업무내용'][:15]}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    updated_df = df.drop(del_idx)
                    save_to_github(updated_df, sha)
                    st.success("삭제 완료!")
                    st.rerun()

        # 목록 출력 및 검색
        st.title("📊 팀 업무일지 대시보드")
        search = st.text_input("🔍 검색어 입력 (날짜, 작성자, 내용 등)")
        
        if search:
            display_df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        else:
            display_df = df

        st.dataframe(display_df, use_container_width=True, hide_index=False)

        # 엑셀 다운로드 버튼 추가
        csv_download = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 전체 기록 엑셀(CSV) 다운로드",
            data=csv_download,
            file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
