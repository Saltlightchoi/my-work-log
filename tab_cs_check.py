import streamlit as st
import pandas as pd
from datetime import datetime
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

        # ==========================================
        # 뷰 1: 상세 작업 화면 (특정 프로젝트 클릭 시)
        # ==========================================
        if st.session_state['view_project_detail'] and st.session_state['view_project_detail'] in project_list:
            selected_proj = st.session_state['view_project_detail']
            
            col_back, col_title = st.columns([1.5, 8.5])
            with col_back:
                st.markdown("<div style='margin-top: 5px;'></div>", unsafe_allow_html=True)
                if st.button("◀ 전체 현황판으로", use_container_width=True):
                    st.session_state['view_project_detail'] = None
                    st.rerun()
            with col_title:
                st.markdown(f"<div class='main-title'>✅ 장비 제작 Flow : 세부 작업 ({selected_proj})</div>", unsafe_allow_html=True)
            
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

            mask = df_flow["프로젝트명"] == selected_proj
            proj_df = df_flow[mask].copy()

            save_col, del_col, empty_col = st.columns([2, 2, 6])
            with save_col: 
                btn_save = st.button("💾 변경 저장", use_container_width=True, type="primary")
            with del_col: 
                if st.button("🗑️ 이 프로젝트 삭제", use_container_width=True):
                    st.session_state['delete_target_proj'] = selected_proj
                    st.rerun()

            if st.session_state.get('delete_target_proj') == selected_proj:
                st.error(f"🚨 [{selected_proj}] 프로젝트를 영구 삭제하시겠습니까?")
                if st.button("⚠️ 삭제 확정", type="primary"):
                    self.db_flow.save(df_flow[~mask])
                    st.session_state['delete_target_proj'] = None
                    st.session_state['view_project_detail'] = None
                    st.rerun()
                if st.button("❌ 취소"): 
                    st.session_state['delete_target_proj'] = None
                    st.rerun()
                st.stop() 

            cats = proj_df['대항목'].unique().tolist()
            with st.expander("⚙️ 프로젝트 대항목 관리 (추가/수정/삭제/순서변경)"):
                c1, c2, c3, c4 = st.tabs(["➕ 대항목 추가", "✏️ 이름 수정", "❌ 대항목 삭제", "↕️ 순서 변경"])
                
                with c1:
                    with st.form("add_cat_form", clear_on_submit=True):
                        new_c = st.text_input("새 대항목 이름")
                        if st.form_submit_button("추가하기") and new_c and new_c not in cats:
                            new_row = pd.DataFrame([{"프로젝트명": selected_proj, "대항목": new_c, "순서": 1, "작업내용": "새 작업 내용 입력", "상태": "⬜ 대기", "비고": "", "첨부": "", "업데이트일": ""}])
                            self.db_flow.save(pd.concat([df_flow, new_row], ignore_index=True))
                            st.success(f"'{new_c}' 항목 추가 완료")
                            st.rerun()

                with c2:
                    with st.form("edit_cat_form", clear_on_submit=True):
                        target_c = st.selectbox("수정할 대항목 선택", cats)
                        rename_c = st.text_input("새로운 이름 입력")
                        if st.form_submit_button("이름 변경") and rename_c and rename_c not in cats:
                            df_flow.loc[(df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == target_c), "대항목"] = rename_c
                            self.db_flow.save(df_flow)
                            st.success("이름 변경 완료")
                            st.rerun()

                with c3:
                    with st.form("del_cat_form"):
                        del_c = st.selectbox("삭제할 대항목 선택", cats)
                        st.warning("⚠️ 해당 대항목과 세부 작업이 영구 삭제됩니다.")
                        if st.form_submit_button("삭제 실행"):
                            df_flow = df_flow[~((df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == del_c))]
                            self.db_flow.save(df_flow)
                            st.success("삭제 완료")
                            st.rerun()

                with c4:
                    st.write("표 안의 **'새 순서'** 숫자를 클릭하여 변경하세요.")
                    order_df = pd.DataFrame({"대항목": cats, "새 순서": range(1, len(cats)+1)})
                    edited_order = st.data_editor(order_df, hide_index=True, use_container_width=True)
                    if st.button("변경된 순서 적용하기"):
                        edited_order = edited_order.sort_values("새 순서")
                        ordered_cats = edited_order["대항목"].tolist()
                        proj_df['__cat_order__'] = pd.Categorical(proj_df['대항목'], categories=ordered_cats, ordered=True)
                        sorted_proj_df = proj_df.sort_values(['__cat_order__', '순서']).drop(columns=['__cat_order__'])
                        new_df_flow = df_flow[df_flow["프로젝트명"] != selected_proj]
                        new_df_flow = pd.concat([new_df_flow, sorted_proj_df], ignore_index=True)
                        self.db_flow.save(new_df_flow)
                        st.success("순서 적용 완료")
                        st.rerun()

            total_tasks = len(proj_df); comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
            pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
            st.markdown(f"<div style='font-size:16px; font-weight:bold; color:#4CAF50;'>⚡ 해당 호기 진행도 ({comp_tasks} / {total_tasks})</div>", unsafe_allow_html=True)
            st.progress(pct_float, text=f"{int(pct_float * 100)}% 완료")
