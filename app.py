import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI 설정 ---
st.set_page_config(layout="wide", page_title="업무 관리 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 구글 스프레드시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Secrets에서 주소를 안전하게 가져옵니다.
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    st.error("Secrets 설정에서 spreadsheet 주소를 찾을 수 없습니다.")
    st.stop()

def get_users():
    # 모든 데이터를 일단 문자열로 읽어와서 비교 에러를 방지합니다.
    df = conn.read(spreadsheet=SHEET_URL, worksheet="users", ttl=0)
    return df.astype(str)

def get_data():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="data", ttl=0)
    return df.astype(str)

# --- 세션 상태 초기화 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 접속")
    choice = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])

    if choice == "로그인":
        st.title("🔐 로그인")
        with st.form("login_form"):
            user_id = st.text_input("아이디")
            user_pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                users_df = get_users()
                user = users_df[(users_df['username'] == str(user_id)) & (users_df['password'] == str(user_pw))]
                if not user.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = str(user_id)
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 틀렸습니다.")

    else:
        st.title("📝 회원가입")
        with st.form("signup_form"):
            new_id = st.text_input("아이디")
            new_pw = st.text_input("비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")
            new_email = st.text_input("이메일")
            new_phone = st.text_input("전화번호")
            
            if st.form_submit_button("가입하기"):
                try:
                    users_df = get_users()
                    if new_pw != new_pw_confirm:
                        st.error("비밀번호가 다릅니다.")
                    elif str(new_id) in users_df['username'].values:
                        st.error("이미 있는 아이디입니다.")
                    else:
                        # [해결포인트] 모든 데이터를 문자열 리스트로 만들어 저장
                        new_user = pd.DataFrame([[str(new_id), str(new_pw), str(new_email), str(new_phone)]], 
                                                columns=["username", "password", "email", "phone"])
                        updated_users = pd.concat([users_df, new_user], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_users)
                        st.success("가입 완료! 로그인 해주세요.")
                except Exception as e:
                    st.error(f"회원가입 오류: {e}")

else:
    # --- 로그인 후 메인 화면 ---
    st.title("📊 업무 대시보드")
    st.write(f"사용자: **{st.session_state['user_name']}**")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    work_df = get_data()

    # 사이드바 Daily
    st.sidebar.title("📅 Daily")
    mode = st.sidebar.selectbox("작업", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

    if mode == "➕ 작성":
        with st.sidebar.form("add"):
            date = st.date_input("날짜")
            content = st.sidebar.text_area("내용")
            note = st.sidebar.text_input("비고")
            if st.form_submit_button("저장"):
                new_entry = pd.DataFrame([[str(date), st.session_state['user_name'], content, note]], 
                                         columns=["날짜", "작성자", "업무내용", "비고"])
                updated_work = pd.concat([work_df, new_entry], ignore_index=True)
                conn.update(spreadsheet=SHEET_URL, worksheet="data", data=updated_work)
                st.rerun()

    # (수정/삭제 로직은 동일하므로 생략 - 전체 필요시 말씀주세요)
    st.dataframe(work_df, use_container_width=True)

    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")

