import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS

class WorkLogTab:
    def __init__(self, db_log):
        self.db_log = db_log

    def render(self):
        df_log, sha_log = self.db_log.load()
        if not df_log.empty and '날짜' in df_log.columns:
            df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
            df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📝 일지 작성/수정/삭제")
        mode = st.sidebar.selectbox("기능 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
        
        if mode == "➕ 작성":
            with st.sidebar.form("add_log", clear_on_submit=True):
                d = st.date_input("날짜", datetime.today())
                e = st.selectbox("장비", EQUIPMENT_OPTIONS)
                c = st.text_area("업무 내용", height=300)
                n = st.text_input("비고")
                a = st.text_input("첨부 (FTP 경로 등)")
                if st.form_submit_button("저장하기"):
                    new_row = pd.DataFrame([{"날짜": str(d), "장비": e, "작성자": st.session_state['user_name'], "업무내용": c, "비고": n, "첨부": a}])
                    self.db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d}")
                    st.rerun()

        elif mode == "✏️ 수정" and not df_log.empty:
            idx = st.sidebar.selectbox("수정 대상", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:15]}...")
            with st.sidebar.form("edit_log"):
                e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[idx, '날짜']))
                e_content = st.text_area("내용 수정", value=df_log.loc[idx, '업무내용'], height=300)
                
                val_note = df_log.loc[idx, '비고'] if '비고' in df_log.columns else ""
                val_note = "" if pd.isna(val_note) else str(val_note)
                e_note = st.text_input("비고 수정", value=val_note)
                
                val_attach = df_log.loc[idx, '첨부'] if '첨부' in df_log.columns else ""
                val_attach = "" if pd.isna(val_attach) else str(val_attach)
                e_attach = st.text_input("첨부 수정", value=val_attach)
                
                if st.form_submit_button("수정 완료"):
                    df_log.loc[idx, ['날짜', '업무내용', '비고', '첨부']] = [str(e_date), e_content, e_note, e_attach]
                    self.db_log.save(df_log, sha_log, "Edit Log")
                    st.rerun()

        elif mode == "❌ 삭제" and not df_log.empty:
            idx = st.sidebar.selectbox("삭제 대상 선택", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:10]}")
            st.sidebar.warning(f"내용: {df_log.loc[idx, '업무내용'][:50]}...")
            if st.sidebar.button("🗑️ 최종 삭제 (복구 불가)", type="primary"):
                self.db_log.save(df_log.drop(idx), sha_log, "Delete Log")
                st.rerun()

        col_title, col_excel = st.columns([8.5, 1.5])
        with col_title:
            st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        with col_excel:
            csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
        
        filter_col1, filter_col2 = st.columns([2, 8])
        with filter_col1:
            equip_filter = st.selectbox("📌 장비모델 필터", ["전체"] + EQUIPMENT_OPTIONS)
        with filter_col2:
            search = st.text_input("🔍 내용/작성자 검색", placeholder="검색어를 입력하세요...")
            
        disp = df_log.copy()
        
        if equip_filter != "전체":
            disp = disp[disp['장비'].astype(str) == equip_filter]
            
        if search: 
            disp = disp[disp.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
        
        st.dataframe(
            disp, 
            use_container_width=True, 
            hide_index=True, 
            column_config={
                "업무내용": st.column_config.TextColumn("업무내용", width="large"),
                "비고": st.column_config.TextColumn("비고", width="small"),
                "첨부": st.column_config.TextColumn("첨부", width="small")
            }
        )
