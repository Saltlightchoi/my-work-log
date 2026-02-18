import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI 설정 및 여백 제거 ---
st.set_page_config(layout="wide", page_title="업무 관리 시스템")

st.markdown("""
    <style>
        /* 메인 및 사이드바 상단 여백 제거 */
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        
        /* 사이드바 우측 이동 및 넓이 조절 */
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        
        /* 사이드바 위치에 따른 메인 화면 여백 조정 */
        .main .block-container { margin-right: 420px; margin-left: 0; }
        
        /* 삭제 확인 박스 스타일 */
        .delete-box {
            padding: 15px; border: 1px solid #ff4b4b;
            border-radius: 5px; background-color: #fff1f1;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 구글 스프레드시트 연결 (Secrets 참조) ---
# 따로 SHEET_URL 변수를 정의하지 않아도 Secrets의 설정을 자동으로 읽습니다.
conn = st.connection("gsheets", type=GSheetsConnection)

def get_users():
    return conn.read(worksheet="users", ttl=0) # ttl=0은 실시간 데이터를 가져오기 위함입니다.

def get_data():
    return conn.read(worksheet="data", ttl=0)

def save_users(df):
    conn.update(worksheet="users", data=df)

def save_data(df):
    conn.update(worksheet="data", data=df)

# --- 세션 상태 초기화 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 접속")
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴를 선택하세요", menu)

    if choice == "로그인":
        st.title("🔐 업무 시스템 로그인")
        with st.form("login_form"):
            user_id = st.text_input("아이디")
            user_pw = st.text_input("비밀번호", type="password")
            if st.form_submit_button("로그인"):
                users_df = get_users()
                # ID와 PW가 일치하는 행 찾기
                user = users_df[(users_df['username'].astype(str) == user_id) & 
                                (users_df['password'].astype(str) == user_pw)]
                if not user.empty:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = user_id
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    else:
        st.title("📝 신규 회원가입")
        with st.form("signup_form"):
            new_id = st.text_input("아이디 (ID)")
            new_pw = st.text_input("비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")
            new_email = st.text_input("이메일 주소")
            new_phone = st.text_input("전화번호")
            
            if st.form_submit_button("가입하기"):
                users_df = get_users()
                if new_pw != new_pw_confirm:
                    st.error("비밀번호가 서로 다릅니다.")
                elif new_id in users_df['username'].astype(str).values:
                    st.error("이미 사용 중인 아이디입니다.")
                elif not (new_id and new_pw and new_email):
                    st.error("필수 항목을 모두 입력해주세요.")
                else:
                    new_user = pd.DataFrame([[new_id, new_pw, new_email, new_phone]], 
                                            columns=["username", "password", "email", "phone"])
                    updated_users = pd.concat([users_df, new_user], ignore_index=True)
                    save_users(updated_users)
                    st.success("회원가입 완료! 로그인 메뉴를 이용해주세요.")

else:
    # --- 로그인 성공 후 메인 서비스 ---
    st.title("📊 팀 업무일지 시스템")
    st.write(f"현재 접속자: **{st.session_state['user_name']}**")
    
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    work_df = get_data()

    # --- 우측 사이드바: Daily ---
    st.sidebar.title("📅 Daily")
    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

    if mode == "➕ 작성":
        with st.sidebar.form("add_form"):
            date = st.date_input("날짜", datetime.today())
            author = st.text_input("작성자", value=st.session_state['user_name'], disabled=True)
            content = st.sidebar.text_area("업무 내용")
            note = st.sidebar.text_input("비고")
            if st.form_submit_button("저장하기"):
                if content:
                    new_entry = pd.DataFrame([[str(date), author, content, note]], 
                                             columns=["날짜", "작성자", "업무내용", "비고"])
                    updated_work = pd.concat([work_df, new_entry], ignore_index=True)
                    save_data(updated_work)
                    st.rerun()
                else:
                    st.sidebar.error("내용을 입력해주세요.")

    elif mode == "✏️ 수정":
        if not work_df.empty:
            edit_idx = st.sidebar.selectbox("수정 대상 선택", options=work_df.index,
                                          format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}...")
            with st.sidebar.form("edit_form"):
                e_date = st.date_input("날짜 수정", value=datetime.strptime(str(work_df.loc[edit_idx, '날짜']), '%Y-%m-%d'))
                e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "업무내용"])
                e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "비고"])
                if st.form_submit_button("수정 완료"):
                    work_df.loc[edit_idx, ["날짜", "업무내용", "비고"]] = [str(e_date), e_content, e_note]
                    save_data(work_df)
                    st.rerun()

    elif mode == "❌ 삭제":
        if not work_df.empty:
            del_idx = st.sidebar.selectbox("삭제 대상 선택", options=work_df.index,
                                         format_func=lambda x: f"[{x}] {work_df.iloc[x]['날짜']} | {work_df.iloc[x]['작성자']}")
            
            selected_row = work_df.loc[del_idx]
            st.sidebar.markdown(f"""
            <div class='delete-box'>
                <strong>삭제 항목 정보:</strong><br>
                📅 날짜: {selected_row['날짜']}<br>
                📝 내용: {selected_row['업무내용']}<br>
            </div>
            """, unsafe_allow_html=True)
            
            if st.sidebar.button("🗑️ 최종 삭제하기", use_container_width=True):
                work_df = work_df.drop(del_idx)
                save_data(work_df)
                st.rerun()

    # --- 메인 화면: 데이터 조회 및 검색 ---
    search_keyword = st.text_input("🔍 검색어 입력")
    if search_keyword:
        display_df = work_df[work_df.apply(lambda r: search_keyword.lower() in str(r).lower(), axis=1)]
    else:
        display_df = work_df

    st.subheader("📋 전체 업무 기록")
    st.dataframe(display_df, use_container_width=True, hide_index=False)
