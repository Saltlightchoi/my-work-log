import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import DataManager
from tab_work_log import WorkLogTab
# ... 다른 탭 임포트 ...

SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"
db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])

st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

menu = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu == "📝 업무일지":
    df = db_work_log.load()
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    st.sidebar.header("🔍 검색 및 필터링")
    date_range = st.sidebar.date_input("날짜 범위", value=(datetime.now() - timedelta(weeks=2), datetime.now()))
    equip_filter = st.sidebar.multiselect("장비 선택", options=df['장비'].unique() if '장비' in df.columns else [])
    keyword = st.sidebar.text_input("내용 검색")

    # 필터 적용
    mask = (df['날짜'].dt.date >= date_range[0]) & (df['날짜'].dt.date <= date_range[1])
    filtered_df = df.loc[mask]
    if equip_filter: filtered_df = filtered_df[filtered_df['장비'].isin(equip_filter)]
    if keyword: filtered_df = filtered_df[filtered_df['업무내용'].str.contains(keyword, na=False)]
    
    # 필터링된 데이터만 넘김
    WorkLogTab(db_work_log).render(filtered_df)
# ... 나머지 메뉴 동일 ...
