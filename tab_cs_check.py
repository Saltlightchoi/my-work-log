import streamlit as st
import pandas as pd
from datetime import datetime
from config import CS_TEMPLATE, maintain_project_order, get_row_color, EQUIPMENT_OPTIONS

class CSCheckSheetTab:
    def __init__(self, db_flow):
        self.db_flow = db_flow

    def render(self):
        df_flow, _ = self.db_flow.load()
        if 'view_project_detail' not in st.session_state: st.session_state['view_project_detail'] = None

        # 에러 방지용 안전 코드
        project_list = df_flow["프로젝트명"].dropna().unique().tolist() if not df_flow.empty and "프로젝트명" in df_flow.columns else []

        if st.session_state['view_project_detail'] and st.session_state['view_project_detail'] in project_list:
            selected_proj = st.session_state['view_project_detail']
            if st.button("◀ 전체 현황판으로"):
                st.session_state['view_project_detail'] = None
                st.rerun()
            st.subheader(f"✅ 상세 작업: {selected_proj}")
            mask = df_flow["프로젝트명"] == selected_proj
            st.dataframe(df_flow[mask], use_container_width=True)
        else:
            st.subheader("✅ 장비 제작 Flow 전체 현황판")
            if not project_list: st.info("프로젝트가 없습니다.")
            else:
                for proj in project_list:
                    if st.button(f"🔍 {proj} 상세 보기", key=proj):
                        st.session_state['view_project_detail'] = proj
                        st.rerun()
