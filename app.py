import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 1. UI 및 스타일 설정 ---
st.set_page_config(layout="wide", page_title="Daily 업무 관리")

st.markdown("""
    <style>
        /* 상단 여백 제거 */
        .block-container { padding-top: 1rem; }
        /* 사이드바 우측 이동 및 넓이 조절 */
        [data-testid="stSidebar"] { left: auto; right: 0; width: 420px !important; }
        /* 메인 화면 여백 조정 */
        .main .block-container { margin-right: 420px; margin-left: 0; }
        /* 삭제 강조 박스 */
        .delete-box { padding: 15px; border: 1px solid #ff4b4b; border-radius: 5px; background-color: #fff1f1; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 구글 시트 연결 설정 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Secrets에서 주소를 안전하게 가져옵니다.
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    st.error("Secrets 설정에서 구글 시트 주소를 찾을 수 없습니다.")
    st.stop()

def get_data():
    # 데이터를 읽어올 때 문자열(str)로 강제 변환하여 비교 에러 방지
    df = conn.read(spreadsheet=SHEET_URL, worksheet="data", ttl=0)
    return df.fillna("").astype(str)

# --- 3. 세션 관리 (단순 로그인) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    st.info("별도의 가입 없이, 본인의 성함(ID)을 입력하고 접속하세요.")
    
    with st.form("login_simple"):
        input_id = st.text_input("접속 아이디 (이름)")
        if st.form_submit_button("입장하기"):
            if input_id:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = input_id
                st.rerun()
            else:
                st.error("아이디(이름)를 입력해주세요.")

else:
    # --- 4. 메인 시스템 (데이터 전용) ---
    st.title("📊 팀 업무일지 대시보드")
    st.write(f"사용자: **{st.session_state['user_name']}**님 환영합니다!")
    
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        work_df = get_data()

        st.sidebar.title("📅 Daily")
        mode = st.sidebar.selectbox("작업", ["➕ 작성", "✏️ 수정", "❌ 삭제"])

        if mode == "➕ 작성":
            with st.sidebar.form("add_log"):
                date = st.date_input("날짜", datetime.today())
                author = st.text_input("작성자", value=st.session_state['user_name'], disabled=True)
                content = st.sidebar.text_area("업무 내용")
                note = st.sidebar.text_input("비고")
                
                if st.form_submit_button("저장하기"):
                    if content:
                        # 신규 데이터 생성
                        new_log = pd.DataFrame([{"날짜":str(date), "작성자":author, "업무내용":content, "비고":note}])
                        # 기존 데이터와 합치기
                        updated = pd.concat([work_df, new_log], ignore_index=True)
                        # 구글 시트 업데이트
                        conn.update(spreadsheet=SHEET_URL, worksheet="data", data=updated)
                        st.success("저장되었습니다!")
                        st.rerun()
                    else:
                        st.sidebar.error("내용을 입력해 주세요.")

        elif mode == "✏️ 수정":
            if not work_df.empty:
                edit_idx = st.sidebar.selectbox("수정할 항목", options=work_df.index,
                                              format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['작성자']}")
                with st.sidebar.form("edit_log"):
                    e_content = st.text_area("내용 수정", value=work_df.loc[edit_idx, "업무내용"])
                    e_note = st.text_input("비고 수정", value=work_df.loc[edit_idx, "비고"])
                    if st.form_submit_button("수정 완료"):
                        work_df.loc[edit_idx, ["업무내용", "비고"]] = [e_content, e_note]
                        conn.update(spreadsheet=SHEET_URL, worksheet="data", data=work_df)
                        st.rerun()

        elif mode == "❌ 삭제":
            if not work_df.empty:
                del_idx = st.sidebar.selectbox("삭제할 항목", options=work_df.index,
                                             format_func=lambda x: f"{work_df.iloc[x]['날짜']} | {work_df.iloc[x]['업무내용'][:15]}")
                st.sidebar.markdown(f"<div class='delete-box'><strong>삭제 확인:</strong> {work_df.loc[del_idx, '업무내용'][:30]}...</div>", unsafe_allow_html=True)
                if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                    work_df = work_df.drop(del_idx)
                    conn.update(spreadsheet=SHEET_URL, worksheet="data", data=work_df)
                    st.rerun()

        # 목록 출력 및 검색
        search = st.text_input("🔍 검색어 입력")
        if search:
            display_df = work_df[work_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        else:
            display_df = work_df

        st.subheader("📋 전체 업무 기록")
        st.dataframe(display_df, use_container_width=True, hide_index=False)

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
