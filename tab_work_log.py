import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS

class WorkLogTab:
    def __init__(self, db_log):
        self.db_log = db_log

    def render(self, df):
        # 데이터 수정/삭제를 위해 원본을 별도 로드
        df_log = self.db_log.load()
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📝 일지 관리")
        mode = st.sidebar.selectbox("기능 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
        
        if mode == "➕ 작성":
            with st.sidebar.form("add_log", clear_on_submit=True):
                d, e = st.date_input("날짜", datetime.today()), st.selectbox("장비", EQUIPMENT_OPTIONS)
                c, n, a = st.text_area("업무 내용", height=200), st.text_input("비고"), st.text_input("첨부")
                if st.form_submit_button("저장하기"):
                    new_row = pd.DataFrame([{"날짜": str(d), "장비": e, "작성자": "본인", "업무내용": c, "비고": n, "첨부": a}])
                    self.db_log.save(pd.concat([df_log, new_row], ignore_index=True))
                    st.rerun()

        elif mode == "✏️ 수정" and not df_log.empty:
            idx = st.sidebar.selectbox("수정 대상", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:10]}")
            with st.sidebar.form("edit_log"):
                e_date = st.date_input("날짜", pd.to_datetime(df_log.loc[idx, '날짜']))
                e_equip = st.selectbox("장비", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df_log.loc[idx, '장비']) if df_log.loc[idx, '장비'] in EQUIPMENT_OPTIONS else 0)
                e_content = st.text_area("내용", value=df_log.loc[idx, '업무내용'])
                if st.form_submit_button("수정 완료"):
                    df_log.loc[idx, ['날짜', '장비', '업무내용']] = [str(e_date), e_equip, e_content]
                    self.db_log.save(df_log)
                    st.rerun()

        elif mode == "❌ 삭제" and not df_log.empty:
            idx = st.sidebar.selectbox("삭제 대상", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:10]}")
            if st.sidebar.button("🗑️ 최종 삭제"):
                self.db_log.save(df_log.drop(idx))
                st.rerun()

        st.subheader("📝 팀 업무일지 대시보드")
        st.dataframe(df, use_container_width=True, hide_index=True)
