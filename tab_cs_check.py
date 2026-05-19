import streamlit as st
import pandas as pd
from config import CS_TEMPLATE, maintain_project_order, get_row_color, EQUIPMENT_OPTIONS

class CSCheckSheetTab:
    def __init__(self, db_flow):
        self.db_flow = db_flow

    def render(self):
        df_flow, _ = self.db_flow.load()
        
        if 'view_project_detail' not in st.session_state:
            st.session_state['view_project_detail'] = None

        if not df_flow.empty and "프로젝트명" in df_flow.columns:
            project_list = df_flow["프로젝트명"].dropna().unique().tolist()
        else:
            project_list = []

        # 상세 작업 화면 뷰
        if st.session_state['view_project_detail'] and st.session_state['view_project_detail'] in project_list:
            selected_proj = st.session_state['view_project_detail']
            if st.button("◀ 전체 현황판으로"):
                st.session_state['view_project_detail'] = None
                st.rerun()
            
            mask = df_flow["프로젝트명"] == selected_proj
            proj_df = df_flow[mask].copy()
            st.subheader(f"✅ 세부 작업: {selected_proj}")
            st.dataframe(proj_df, use_container_width=True)

        # 전체 현황판 뷰
        else:
            st.subheader("✅ 장비 제작 Flow 전체 현황판")
            if not project_list:
                st.info("현재 프로젝트가 없습니다.")
            else:
                for proj in project_list:
                    if st.button(f"🔍 {proj} 상세 보기", key=proj):
                        st.session_state['view_project_detail'] = proj
                        st.rerun()
