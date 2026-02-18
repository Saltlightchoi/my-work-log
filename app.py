import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI 설정 ---
st.set_page_config(layout="wide", page_title="Daily 업무 관리")

# --- 구글 시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # 데이터를 읽어올 때 헤더를 기준으로 읽어오되, 오류를 방지하기 위해 빈 데이터프레임 생성을 대비합니다.
    try:
        df = conn.read(worksheet="data", ttl=0)
        return df.fillna("").astype(str)
    except:
        # 시트가 완전히 비어있을 경우 기본 틀을 만듭니다.
        return pd.DataFrame(columns=['date', 'author', 'content', 'note'])

# --- 세션 관리 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

# --- 메인 로직 ---
if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login"):
        name = st.text_input("성함을 입력하세요")
        if st.form_submit_button("입장하기"):
            if name:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = name
                st.rerun()
else:
    st.title(f"📊 {st.session_state['user_name']}님의 업무 대시보드")
    if st.button("로그아웃"):
        st.session_state['logged_in'] = False
        st.rerun()

    try:
        work_df = get_data()

        st.sidebar.title("📅 일지 작성")
        with st.sidebar.form("add_form"):
            d = st.date_input("날짜", datetime.today())
            c = st.text_area("업무 내용")
            n = st.text_input("비고")
            if st.form_submit_button("저장하기"):
                if c:
                    # [해결포인트] 데이터 형식을 구글 시트가 가장 좋아하는 딕셔너리 리스트 형태로 전달
                    new_data = {
                        "date": [str(d)],
                        "author": [st.session_state['user_name']],
                        "content": [str(c)],
                        "note": [str(n)]
                    }
                    new_df = pd.DataFrame(new_data)
                    
                    # 기존 데이터에 붙이기
                    updated_df = pd.concat([work_df, new_df], ignore_index=True)
                    
                    # 업데이트 실행
                    conn.update(worksheet="data", data=updated_df)
                    st.success("성공적으로 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("내용을 입력해주세요.")

        # 테이블 출력
        st.subheader("📋 전체 기록")
        st.dataframe(work_df, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ 연동 오류: {e}")
        st.info("구글 시트의 2행부터 모든 빈 행을 '삭제'한 뒤 다시 시도해 보세요.")
