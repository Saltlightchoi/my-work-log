import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# 파일 및 DB 설정
DATA_FILE = "work_log.csv"
DB_FILE = "users.db"

# --- 데이터베이스 및 데이터 관리 함수 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, phone TEXT)''')
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, engine='python')
    else:
        return pd.DataFrame(columns=["날짜", "작성자", "업무내용", "비고"])

def save_all_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- UI 설정 ---
st.set_page_config(layout="wide", page_title="업무 관리 시스템")
init_db()

# CSS: 사이드바 및 여백 설정
st.markdown("""
    <style>
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; padding-top: 1rem; }
        /* 삭제 확인 박스 스타일 */
        .delete-box {
            padding: 15px;
            border: 1px solid #ff4b4b;
            border-radius: 5px;
            background-color: #fff1f1;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)
    # (로그인/회원가입 로직은 이전과 동일하므로 생략하거나 기존 코드 유지 가능)
    # ... [생략된 로그인/가입 코드] ...
    if choice == "로그인":
        st.title("🔐 로그인")
        with st.form("login"):
            uid = st.text_input("아이디")
            upw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                if check_login(uid, upw):
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = uid
                    st.rerun()
                else: st.error("정보 불일치")
else:
    # --- 로그인 성공 후 ---
    st.title("📊 팀 업무일지 시스템")
    st.write(f"접속자: **{st.session_state['user_name']}**")
    
    df = load_data()

    # --- 사이드바: Daily ---
    st.sidebar.title("📅 Daily")
    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

    # [➕ 작성 / ✏️ 수정 로직은 기존과 동일]
    if mode == "➕ 작성":
        with st.sidebar.form("new_form"):
            date = st.date_input("날짜", datetime.today())
            author = st.sidebar.text_input("작성자", value=st.session_state['user_name'], disabled=True)
            content = st.sidebar.text_area("업무 내용")
            note = st.sidebar.text_input("비고")
            if st.form_submit_button("저장"):
                if content:
                    new_row = pd.DataFrame({"날짜": [str(date)], "작성자": [author], "업무내용": [content], "비고": [note]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_all_data(df)
                    st.rerun()

    elif mode == "✏️ 수정":
        if not df.empty:
            edit_idx = st.sidebar.selectbox("수정 대상", options=df.index, 
                                          format_func=lambda x: f"{df.iloc[x]['날짜']} | {df.iloc[x]['작성자']} | {df.iloc[x]['업무내용'][:15]}...")
            with st.sidebar.form("edit_form"):
                e_date = st.date_input("날짜", datetime.strptime(str(df.loc[edit_idx, "날짜"]), '%Y-%m-%d'))
                e_content = st.text_area("업무 내용", value=df.loc[edit_idx, "업무내용"])
                e_note = st.text_input("비고", value=df.loc[edit_idx, "비고"])
                if st.form_submit_button("수정 완료"):
                    df.loc[edit_idx, ["날짜", "업무내용", "비고"]] = [str(e_date), e_content, e_note]
                    save_all_data(df)
                    st.rerun()

    # --- ❌ 삭제 섹션 (요청하신 개선 부분) ---
    elif mode == "❌ 삭제":
        if not df.empty:
            st.sidebar.subheader("삭제 항목 선택")
            
            # 드롭다운에 날짜와 내용을 함께 표시
            delete_idx = st.sidebar.selectbox(
                "삭제할 일지를 선택하세요", 
                options=df.index,
                format_func=lambda x: f"[{x}] {df.iloc[x]['날짜']} - {df.iloc[x]['작성자']} ({df.iloc[x]['업무내용'][:10]}...)"
            )
            
            # 선택한 항목의 상세 내용을 사이드바에 미리보기로 출력
            selected_row = df.loc[delete_idx]
            st.sidebar.markdown(f"""
            <div class='delete-box'>
                <strong>선택된 항목 상세:</strong><br>
                📅 날짜: {selected_row['날짜']}<br>
                👤 작성자: {selected_row['작성자']}<br>
                📝 내용: {selected_row['업무내용']}<br>
                📌 비고: {selected_row['비고']}
            </div>
            """, unsafe_allow_html=True)
            
            st.sidebar.warning("⚠️ 삭제된 데이터는 복구할 수 없습니다.")
            if st.sidebar.button("🗑️ 최종 삭제하기", use_container_width=True):
                df = df.drop(delete_idx)
                save_all_data(df)
                st.sidebar.success("성공적으로 삭제되었습니다.")
                st.rerun()
        else:
            st.sidebar.info("삭제할 데이터가 없습니다.")

    # --- 메인 화면 목록 및 검색 ---
    search = st.text_input("🔍 검색어 입력")
    display_df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)] if search else df
    st.subheader("📋 전체 업무 기록")
    st.dataframe(display_df, use_container_width=True)
