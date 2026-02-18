import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI 및 설정 ---
st.set_page_config(layout="wide", page_title="업무 관리 시스템")

# 구글 스프레드시트 연결 설정 (시트 URL을 입력하세요)
SHEET_URL = https://docs.google.com/spreadsheets/d/1vzUWmoyOgo1TwahtedmncfXhEL7kiNIfpjh0t4jvn0k/edit?usp=drivesdk

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 및 저장 함수 ---
def get_users():
    return conn.read(spreadsheet=SHEET_URL, worksheet="users")

def get_data():
    return conn.read(spreadsheet=SHEET_URL, worksheet="data")

def save_users(df):
    conn.update(spreadsheet=SHEET_URL, worksheet="users", data=df)

def save_data(df):
    conn.update(spreadsheet=SHEET_URL, worksheet="data", data=df)

# --- CSS: 사이드바 우측 이동 ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "로그인":
        st.title("🔐 로그인")
        with st.form("login_form"):
            user_id = st.text_input("아이디")
            user_pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                users_df = get_users()
                user = users_df[(users_df['username'] == user_id) & (users_df['password'] == user_pw)]
                if not user.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_id
                    st.rerun()
                else:
                    st.error("정보가 일치하지 않습니다.")

    else:
        st.title("📝 회원가입")
        with st.form("signup_form"):
            new_id = st.text_input("아이디")
            new_pw = st.text_input("비밀번호", type="password")
            new_email = st.text_input("이메일")
            new_phone = st.text_input("전화번호")
            if st.form_submit_button("가입하기"):
                users_df = get_users()
                if new_id in users_df['username'].values:
                    st.error("이미 존재하는 아이디입니다.")
                else:
                    new_user = pd.DataFrame([[new_id, new_pw, new_email, new_phone]], 
                                            columns=["username", "password", "email", "phone"])
                    updated_users = pd.concat([users_df, new_user], ignore_index=True)
                    save_users(updated_users)
                    st.success("가입 완료! 로그인 해주세요.")

else:
    # --- 로그인 후 서비스 ---
    st.title(f"📊 {st.session_state['user_name']}님의 업무 시스템")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    work_df = get_data()

    # --- 사이드바: Daily ---
    st.sidebar.title("📅 Daily")
    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

    if mode == "➕ 작성":
        with st.sidebar.form("add_form"):
            date = st.date_input("날짜", datetime.today())
            content = st.sidebar.text_area("업무 내용")
            note = st.sidebar.text_input("비고")
            if st.form_submit_button("저장"):
                new_entry = pd.DataFrame([[str(date), st.session_state['user_name'], content, note]], 
                                         columns=["날짜", "작성자", "업무내용", "비고"])
                updated_work = pd.concat([work_df, new_entry], ignore_index=True)
                save_data(updated_work)
                st.rerun()

    elif mode == "✏️ 수정":
        if not work_df.empty:
            edit_idx = st.sidebar.selectbox("수정 대상", options=work_df.index,
                                          format_func=lambda x: f"{work_df.iloc[x]['날짜']} - {work_df.iloc[x]['업무내용'][:15]}")
            with st.sidebar.form("edit_form"):
                e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "업무내용"])
                e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "비고"])
                if st.form_submit_button("수정 완료"):
                    work_df.loc[edit_idx, "업무내용"] = e_content
                    work_df.loc[edit_idx, "비고"] = e_note
                    save_data(work_df)
                    st.rerun()

    elif mode == "❌ 삭제":
        if not work_df.empty:
            del_idx = st.sidebar.selectbox("삭제 대상", options=work_df.index,
                                         format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}")
            if st.sidebar.button("🗑️ 정말 삭제할까요?"):
                work_df = work_df.drop(del_idx)
                save_data(work_df)
                st.rerun()

    # --- 메인 목록 ---
    st.subheader("📋 전체 목록")
    st.dataframe(work_df, use_container_width=True)

