import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. 화면 스타일 및 여백 설정 ---
st.set_page_config(layout="wide", page_title="Daily 업무 관리")

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        .main .block-container { margin-right: 420px; margin-left: 0; }
        .delete-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 5px; background-color: #fff1f1; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 (Secrets 사용) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # 모든 데이터를 문자열(str)로 읽어와서 형식 오류를 방지합니다.
    df = conn.read(worksheet="data", ttl=0)
    return df.fillna("").astype(str)

# --- 3. 로그인 상태 관리 (성함만 입력) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login_simple"):
        input_id = st.text_input("접속하실 성함을 입력하세요 (ID)")
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
        # 데이터 불러오기
        work_df = get_data()

        # 사이드바 설정
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
                        # 데이터 추가 로직
                        new_row = pd.DataFrame([{"날짜":str(date), "작성자":author, "업무내용":content, "비고":note}])
                        updated_df = pd.concat([work_df, new_row], ignore_index=True)
                        conn.update(worksheet="data", data=updated_df)
                        st.success("저장 완료!")
                        st.rerun()
                    else:
                        st.sidebar.error("내용을 입력해 주세요.")

        elif mode == "✏️ 수정":
            if not work_df.empty:
                edit_idx = st.sidebar.selectbox("수정 대상", options=work_df.index,
                                              format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}")
                with st.sidebar.form("edit_form"):
                    e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "비고"])
                    if st.form_submit_button("수정 완료"):
                        work_df.loc[edit_idx, ["업무내용", "비고"]] = [e_content, e_note]
                        conn.update(worksheet="data", data=work_df)
                        st.rerun()

        elif mode == "❌ 삭제":
            if not work_df.empty:
                del_idx = st.sidebar.selectbox("삭제 대상", options=work_df.index,
                                             format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['작성자']}")
                st.sidebar.markdown(f"<div class='delete-box'><strong>삭제 확인:</strong> {work_df.loc[del_idx, '업무내용'][:30]}...</div>", unsafe_allow_html=True)
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    work_df = work_df.drop(del_idx)
                    conn.update(worksheet="data", data=work_df)
                    st.rerun()

        # 메인 목록 조회 및 검색
        search = st.text_input("🔍 검색어 입력")
        if search:
            display_df = work_df[work_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        else:
            display_df = work_df

        st.subheader("📋 전체 업무 기록")
        st.dataframe(display_df, use_container_width=True, hide_index=False)

    except Exception as e:
        st.error(f"데이터 연동 중 오류가 발생했습니다. 구글 시트의 'data' 탭과 헤더를 확인하세요. (에러: {e})")
