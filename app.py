import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import DataManager
from tab_work_log import WorkLogTab
from tab_cs_check import CSCheckSheetTab
from tab_equipment_data import EquipmentDataTab
from tab_ecn_stn import ECNSTNTab

SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"
db_work_log = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
db_cs_check = DataManager(SPREADSHEET_ID, "CS체크리스트")
db_equipment = DataManager(SPREADSHEET_ID, "장비데이터")
db_ecn = DataManager(SPREADSHEET_ID, "ECN_STN")

st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

menu = st.sidebar.selectbox("메뉴 선택", ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"])

if menu == "📝 업무일지":
    df = db_work_log.load()
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    st.sidebar.header("🔍 검색 및 필터링")
    date_range = st.sidebar.date_input("날짜 범위", value=(datetime.now() - timedelta(weeks=2), datetime.now()))
    equip_filter = st.sidebar.multiselect("장비 선택", options=df['장비'].unique() if '장비' in df.columns else [])
    keyword = st.sidebar.text_input("내용 검색")

    mask = (df['날짜'].dt.date >= date_range[0]) & (df['날짜'].dt.date <= date_range[1])
    filtered_df = df.loc[mask]
    if equip_filter: filtered_df = filtered_df[filtered_df['장비'].isin(equip_filter)]
    if keyword: filtered_df = filtered_df[filtered_df['업무내용'].str.contains(keyword, na=False)]
    
    WorkLogTab(db_work_log).render(filtered_df)

elif menu == "✅ 장비 제작 Flow": CSCheckSheetTab(db_cs_check).render()
elif menu == "📊 장비가동데이터": EquipmentDataTab(db_equipment).render()
elif menu == "🛠️ ECN & STN": ECNSTNTab(db_ecn).render()
