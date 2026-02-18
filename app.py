import streamlit as st
import pandas as pd
import sqlite3
import os
import re
from datetime import datetime

# 파일 및 DB 설정
DATA_FILE = "work_log.csv"
DB_FILE = "users.db"

# --- 데이터베이스 초기화 함수 ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 유저 테이블 생성 (ID, 비밀번호, 이메일, 전화번호)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT, phone TEXT)''')
    conn.commit()
    conn.close()

# --- 회원 관련 함수 ---
def add_user(username, password, email, phone):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, password, email, phone))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # 중복 ID 발생 시

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()
    return user

# --- 업무 데이터 관련 함수 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, engine='python')
    else:
        return pd.DataFrame(columns=["날짜", "작성자", "업무내용", "비고"])

def save_all_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- UI 설정 및 초기화 ---
st.set_page_config(layout="wide", page_title="업무 관리 시스템")
init_db()

# CSS: 사이드바 우측 이동 및 디자인
st.markdown("""
    <style>
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; padding-top: 1rem; }
        .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    # 로그인 / 회원가입 선택
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "로그인":
        st.title("🔐 로그인")
        with st.form("login_form"):
            user_id = st.text_input("아이디")
            user_pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                result = check_login(user_id, user_pw)
                if result:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_id
                    st.success(f"{user_id}님 환영합니다!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

    else:
        st.title("📝 회원가입")
        with st.form("signup_form"):
            new_id = st.text_input("아이디 (ID)")
            new_pw = st.text_input("비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")
            new_email = st.text_input("이메일 주소 (E-Mail)")
            new_phone = st.text_input("전화번호 (Phone)")
            
            submit_signup = st.form_submit_button("가입하기")
            
            if submit_signup:
                if new_pw != new_pw_confirm:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif not (new_id and new_pw and new_email and new_phone):
                    st.error("모든 항목을 입력해 주세요.")
                else:
                    success = add_user(new_id, new_pw, new_email, new_phone)
                    if success:
                        st.success("회원가입이 완료되었습니다! 로그인해 주세요.")
                    else:
                        st.error("이미 존재하는 아이디입니다.")

else:
    # --- 로그인 성공 후 서비스 화면 ---
    st.title("📊 팀 업무일지 시스템")
    st.write(f"사용자: **{st.session_state['user_name']}**")
    
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    df = load_data()

    # --- 사이드바: Daily ---
    st.sidebar.title("📅 Daily")
    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

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
            edit_idx = st.sidebar.selectbox("수정 대상", options=df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['날짜']}")
            with st.sidebar.form("edit_form"):
                e_date = st.date_input("날짜", datetime.strptime(str(df.loc[edit_idx, "날짜"]), '%Y-%m-%d'))
                e_content = st.text_area("업무 내용", value=df.loc[edit_idx, "업무내용"])
                e_note = st.text_input("비고", value=df.loc[edit_idx, "비고"])
                if st.form_submit_button("수정 완료"):
                    df.loc[edit_idx, ["날짜", "업무내용", "비고"]] = [str(e_date), e_content, e_note]
                    save_all_data(df)
                    st.rerun()

    elif mode == "❌ 삭제":
        if not df.empty:
            delete_idx = st.sidebar.selectbox("삭제 대상", options=df.index)
            if st.sidebar.button("정말 삭제하시겠습니까?"):
                df = df.drop(delete_idx)
                save_all_data(df)
                st.rerun()

    # --- 메인 목록 ---
    search = st.text_input("🔍 검색")
    display_df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)] if search else df
    st.dataframe(display_df, use_container_width=True)
