import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI 설정 ---
st.set_page_config(layout="wide", page_title="Daily 업무 관리")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users():
    # 데이터를 읽어올 때 문자열로 강제 변환하여 비교 오류 방지
    df = conn.read(worksheet="users", ttl=0)
    return df.fillna("").astype(str)

def get_data():
    df = conn.read(worksheet="data", ttl=0)
    return df.fillna("").astype(str)

# --- 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 접속")
    choice = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])

    if choice == "로그인":
        st.title("🔐 로그인")
        with st.form("login"):
            uid = st.text_input("아이디")
            upw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                try:
                    udf = get_users()
                    user = udf[(udf['username'] == str(uid)) & (udf['password'] == str(upw))]
                    if not user.empty:
                        st.session_state['logged_in'] = True
                        st.session_state['user_name'] = str(uid)
                        st.rerun()
                    else: st.error("정보가 일치하지 않습니다.")
                except: st.error("데이터를 읽을 수 없습니다. 시트 헤더를 확인하세요.")

    else:
        st.title("📝 회원가입")
        with st.form("signup"):
            nid = st.text_input("아이디")
            npw = st.text_input("비밀번호", type="password")
            nemail = st.text_input("이메일")
            nphone = st.text_input("전화번호")
            if st.form_submit_button("가입하기"):
                try:
                    udf = get_users()
                    if str(nid) in udf['username'].values:
                        st.error("이미 있는 아이디입니다.")
                    else:
                        # 신규 유저 생성 (열 이름을 시트와 완벽히 일치시킴)
                        new_row = pd.DataFrame([{"username":str(nid), "password":str(npw), "email":str(nemail), "phone":str(nphone)}])
                        updated = pd.concat([udf, new_row], ignore_index=True)
                        conn.update(worksheet="users", data=updated)
                        st.success("가입 완료! 로그인 해주세요.")
                except Exception as e:
                    st.error(f"가입 실패: {e}")

else:
    # --- 서비스 화면 ---
    st.title(f"📊 {st.session_state['user_name']}님의 대시보드")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        ddf = get_data()
        st.sidebar.title("📅 Daily")
        mode = st.sidebar.selectbox("작업", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add"):
                date = st.date_input("날짜", datetime.today())
                content = st.sidebar.text_area("내용")
                note = st.sidebar.text_input("비고")
                if st.form_submit_button("저장"):
                    new_log = pd.DataFrame([{"날짜":str(date), "작성자":st.session_state['user_name'], "업무내용":content, "비고":note}])
                    updated = pd.concat([ddf, new_log], ignore_index=True)
                    conn.update(worksheet="data", data=updated)
                    st.rerun()
        
        # 목록 출력 및 검색
        search = st.text_input("🔍 검색")
        show_df = ddf[ddf.apply(lambda r: search.lower() in str(r).lower(), axis=1)] if search else ddf
        st.dataframe(show_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"오류 발생: {e}")
