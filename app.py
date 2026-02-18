import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일명
DATA_FILE = "work_log.csv"

# --- 기능 함수 정의 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE, engine='python')
    else:
        return pd.DataFrame(columns=["날짜", "작성자", "업무내용", "비고"])

def save_all_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- UI 설정 ---
st.set_page_config(layout="wide", page_title="업무일지 시스템")

# CSS: 사이드바 우측 이동 및 넓이 조절
st.markdown("""
    <style>
        /* 1. 사이드바를 오른쪽으로 이동 */
        [data-testid="stSidebar"] {
            left: auto;
            right: 0;
            width: 400px !important; /* 사이드바 넓이를 400px로 설정 (기본은 약 300px) */
        }
        
        /* 2. 메인 콘텐츠 여백 조정 (사이드바가 오른쪽에 있으므로 왼쪽 여백 제거) */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        .main .block-container {
            margin-right: 400px; /* 사이드바 넓이만큼 메인 화면에 오른쪽 여백 부여 */
            margin-left: 0;
            padding-top: 1rem;
        }

        /* 3. 사이드바 내부 여백 조절 */
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 팀 업무일지 시스템")

df = load_data()

# --- 1. 사이드바: Daily (이제 우측에 위치함) ---
st.sidebar.title("📅 Daily")

mode = st.sidebar.selectbox("작업을 선택하세요", ["➕ 새 일지 작성", "✏️ 기존 일지 수정", "❌ 일지 삭제"])

if mode == "➕ 새 일지 작성":
    st.sidebar.subheader("신규 작성")
    with st.sidebar.form("new_form"):
        date = st.date_input("날짜", datetime.today())
        author = st.sidebar.text_input("작성자 이름")
        content = st.sidebar.text_area("주요 업무 내용")
        note = st.sidebar.text_input("비고/특이사항")
        
        if st.form_submit_button("💾 저장하기"):
            if author and content:
                new_row = pd.DataFrame({"날짜": [str(date)], "작성자": [author], "업무내용": [content], "비고": [note]})
                df = pd.concat([df, new_row], ignore_index=True)
                save_all_data(df)
                st.sidebar.success("저장 완료!")
                st.rerun()
            else:
                st.sidebar.error("이름과 내용은 필수입니다.")

elif mode == "✏️ 기존 일지 수정":
    if not df.empty:
        st.sidebar.subheader("내용 수정")
        edit_idx = st.sidebar.selectbox("수정할 항목 번호", options=df.index, 
                                        format_func=lambda x: f"[{x}] {df.iloc[x]['날짜']} - {df.iloc[x]['작성자']}")
        
        with st.sidebar.form("edit_form"):
            e_date = st.date_input("날짜", datetime.strptime(str(df.loc[edit_idx, "날짜"]), '%Y-%m-%d'))
            e_author = st.text_input("작성자 이름", value=df.loc[edit_idx, "작성자"])
            e_content = st.text_area("주요 업무 내용", value=df.loc[edit_idx, "업무내용"])
            e_note = st.text_input("비고/특이사항", value=df.loc[edit_idx, "비고"])
            
            if st.form_submit_button("🔄 수정 완료"):
                df.loc[edit_idx] = [str(e_date), e_author, e_content, e_note]
                save_all_data(df)
                st.sidebar.success("수정 완료!")
                st.rerun()

elif mode == "❌ 일지 삭제":
    if not df.empty:
        st.sidebar.subheader("데이터 삭제")
        delete_idx = st.sidebar.selectbox("삭제할 항목 번호", options=df.index, 
                                          format_func=lambda x: f"[{x}] {df.iloc[x]['날짜']} - {df.iloc[x]['작성자']}")
        
        st.sidebar.warning(f"선택한 {delete_idx}번 항목을 삭제하시겠습니까?")
        if st.sidebar.button("🗑️ 최종 삭제"):
            df = df.drop(delete_idx)
            save_all_data(df)
            st.sidebar.success("삭제 완료!")
            st.rerun()

# --- 2. 메인 화면 ---
if not df.empty:
    search_keyword = st.text_input("🔍 검색어 입력", placeholder="검색어를 입력하세요...")
    
    if search_keyword:
        mask = df.apply(lambda row: row.astype(str).str.contains(search_keyword).any(), axis=1)
        display_df = df[mask]
    else:
        display_df = df

    st.subheader("📋 전체 업무 기록")
    st.dataframe(display_df, use_container_width=True, hide_index=False)
    
    csv = display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button("📥 목록 다운로드 (CSV)", data=csv, file_name="work_log.csv", mime="text/csv")
else:
    st.info("데이터가 없습니다. 오른쪽 Daily 메뉴에서 작성을 시작하세요!")
