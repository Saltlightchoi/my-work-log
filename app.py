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

# --- 2. 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # 모든 데이터를 문자열로 읽어와서 형식 충돌 방지
    df = conn.read(worksheet="data", ttl=0)
    return df.fillna("").astype(str)

# --- 3. 세션 관리 (성함 기반 로그인) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login_form"):
        input_id = st.text_input("성함을 입력하고 입장하세요 (ID)")
        if st.form_submit_button("입장하기"):
            if input_id:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = input_id
                st.rerun()
            else:
                st.error("성함을 입력해 주세요.")
else:
    # --- 4. 메인 대시보드 ---
    st.title("📊 팀 업무일지 대시보드")
    st.write(f"사용자: **{st.session_state['user_name']}**님 환영합니다!")
    
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        work_df = get_data()

        st.sidebar.title("📅 Daily")
        mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add_form"):
                d_val = st.date_input("날짜", datetime.today())
                a_val = st.text_input("작성자", value=st.session_state['user_name'], disabled=True)
                c_val = st.sidebar.text_area("업무 내용")
                n_val = st.sidebar.text_input("비고")
                
                if st.form_submit_button("저장하기"):
                    if c_val:
                        # 1단계에서 수정한 영어 헤더와 일치해야 합니다.
                        new_row = pd.DataFrame([{"date":str(d_val), "author":a_val, "content":c_val, "note":n_val}])
                        updated_df = pd.concat([work_df, new_row], ignore_index=True)
                        conn.update(worksheet="data", data=updated_df)
                        st.success("저장 완료!")
                        st.rerun()
                    else:
                        st.sidebar.error("내용을 입력해 주세요.")

        elif mode == "✏️ 수정":
            if not work_df.empty:
                # 'content' 헤더를 사용하도록 수정
                edit_idx = st.sidebar.selectbox("수정 대상", options=work_df.index,
                                              format_func=lambda x: f"{work_df.iloc[x]['date']} | {work_df.iloc[x]['content'][:15]}")
                with st.sidebar.form("edit_form"):
                    e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "content"])
                    e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "note"])
                    if st.form_submit_button("수정 완료"):
                        work_df.loc[edit_idx, ["content", "note"]] = [e_content, e_note]
                        conn.update(worksheet="data", data=work_df)
                        st.rerun()

        elif mode == "❌ 삭제":
            if not work_df.empty:
                del_idx = st.sidebar.selectbox("삭제 대상", options=work_df.index,
                                             format_func=lambda x: f"{work_df.iloc[x]['date']} | {work_df.iloc[x]['author']}")
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    work_df = work_df.drop(del_idx)
                    conn.update(worksheet="data", data=work_df)
                    st.rerun()

        # 메인 목록 출력 (보기 편하게 한글로 열 이름을 바꿔서 출력)
        search = st.text_input("🔍 검색어 입력")
        display_df = work_df.copy()
        display_df.columns = ["날짜", "작성자", "업무내용", "비고"] # 출력할 때만 한글로 표시
        
        if search:
            display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

        st.subheader("📋 전체 업무 기록")
        st.dataframe(display_df, use_container_width=True, hide_index=False)

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 구글 시트 헤더가 date, author, content, note 인지 확인하세요! (에러: {e})")
