import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. UI 및 스타일 설정 ---
st.set_page_config(layout="wide", page_title="Daily 업무 관리")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; }
        .delete-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 5px; background-color: #fff1f1; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 설정 ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    st.error("Secrets 설정에서 구글 시트 주소를 찾을 수 없습니다.")
    st.stop()

def get_users():
    # 모든 데이터를 문자열(str)로 읽어와 비교 에러 방지
    df = conn.read(spreadsheet=SHEET_URL, worksheet="users", ttl=0)
    return df.fillna("").astype(str)

def get_data():
    df = conn.read(spreadsheet=SHEET_URL, worksheet="data", ttl=0)
    return df.fillna("").astype(str)

# --- 3. 로그인 및 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

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
                # 문자열로 변환하여 비교
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
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif str(new_id) in users_df['username'].values:
                        st.error("이미 존재하는 아이디입니다.")
                    elif not (new_id and new_pw):
                        st.error("아이디와 비밀번호는 필수입니다.")
                    else:
                        new_user = pd.DataFrame([[str(new_id), str(new_pw), str(new_email), str(new_phone)]], 
                                                columns=["username", "password", "email", "phone"])
                        updated_users = pd.concat([users_df, new_user], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="users", data=updated_users)
                        st.success("가입 완료! 로그인 해주세요.")
                except Exception as e:
                    st.error(f"회원가입 오류: {e}")

else:
    # --- 4. 로그인 성공 후 메인 시스템 ---
    st.title("📊 업무 대시보드")
    st.write(f"접속자: **{st.session_state['user_name']}**")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        work_df = get_data()

        st.sidebar.title("📅 Daily")
        mode = st.sidebar.selectbox("작업", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add"):
                date = st.date_input("날짜", datetime.today())
                author = st.text_input("작성자", value=st.session_state['user_name'], disabled=True)
                content = st.sidebar.text_area("내용")
                note = st.sidebar.text_input("비고")
                if st.form_submit_button("저장"):
                    if content:
                        new_entry = pd.DataFrame([[str(date), author, content, note]], 
                                                 columns=["날짜", "작성자", "업무내용", "비고"])
                        updated_work = pd.concat([work_df, new_entry], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, worksheet="data", data=updated_work)
                        st.rerun()
                    else:
                        st.sidebar.error("내용을 입력해 주세요.")

        elif mode == "✏️ 수정":
            if not work_df.empty:
                edit_idx = st.sidebar.selectbox("수정 대상", options=work_df.index,
                                              format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}")
                with st.sidebar.form("edit"):
                    e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "비고"])
                    if st.form_submit_button("수정 완료"):
                        work_df.loc[edit_idx, ["업무내용", "비고"]] = [e_content, e_note]
                        conn.update(spreadsheet=SHEET_URL, worksheet="data", data=work_df)
                        st.rerun()

        elif mode == "❌ 삭제":
            if not work_df.empty:
                del_idx = st.sidebar.selectbox("삭제 대상", options=work_df.index,
                                             format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}")
                if st.sidebar.button("🗑️ 정말 삭제할까요?", use_container_width=True):
                    work_df = work_df.drop(del_idx)
                    conn.update(spreadsheet=SHEET_URL, worksheet="data", data=work_df)
                    st.rerun()

        # 메인 목록 출력
        search = st.text_input("🔍 검색")
        display_df = work_df[work_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)] if search else work_df
        st.dataframe(display_df, use_container_width=True, hide_index=False)

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
