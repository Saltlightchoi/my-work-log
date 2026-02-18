import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 데이터 저장 파일명
DATA_FILE = "work_log.csv"

# --- 기능 함수 정의 ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["날짜", "작성자", "업무내용", "비고"])

def save_data(date, author, content, note):
    new_data = pd.DataFrame({
        "날짜": [date],
        "작성자": [author],
        "업무내용": [content],
        "비고": [note]
    })
    
    if os.path.exists(DATA_FILE):
        new_data.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
    else:
        new_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

# --- 1. 사이드바: 업무 일지 작성 폼 ---
st.sidebar.title("📝 일지 작성")
st.sidebar.markdown("오늘의 업무를 기록하세요.")

with st.sidebar.form("log_form"):
    date = st.date_input("날짜", datetime.today())
    author = st.text_input("작성자 이름")
    content = st.text_area("주요 업무 내용", height=150)
    note = st.text_input("비고/특이사항")
    
    submitted = st.form_submit_button("💾 일지 저장하기")

    if submitted:
        if author and content:
            save_data(date, author, content, note)
            st.sidebar.success("저장 완료!")
            st.rerun() 
        else:
            st.sidebar.error("이름과 내용은 필수입니다.")

# --- 2. 메인 화면: 여기가 빠져 있어서 화면이 안 나왔던 겁니다! ---
st.title("📊 팀 업무일지 대시보드")

df = load_data()

if not df.empty:
    # 최신순 정렬
    df = df.sort_values(by="날짜", ascending=False)

    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        search_keyword = st.text_input("🔍 검색 (작성자, 업무내용, 비고)", placeholder="검색어를 입력하세요...")
    
    if search_keyword:
        mask = (
            df["업무내용"].astype(str).str.contains(search_keyword, na=False) | 
            df["작성자"].astype(str).str.contains(search_keyword, na=False) |
            df["비고"].astype(str).str.contains(search_keyword, na=False)
        )
        display_df = df[mask]
        st.info(f"검색 결과: 총 {len(display_df)}건이 발견되었습니다.")
    else:
        display_df = df 

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    csv_data = display_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.download_button(
        label="📥 목록 다운로드 (CSV)",
        data=csv_data,
        file_name="work_log_export.csv",
        mime="text/csv"
    )

else:
    st.info("👈 왼쪽 사이드바에서 첫 번째 업무일지를 작성해주세요!")