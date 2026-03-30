import streamlit as st
import pandas as pd
from datetime import datetime
from config import CS_TEMPLATE, maintain_project_order, get_row_color

class CSCheckSheetTab:
    def __init__(self, db_flow):
        self.db_flow = db_flow

    def render(self):
        df_flow, sha_flow = self.db_flow.load()
        st.markdown("<div class='main-title'>✅ CS 작업 체크 시트</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
        
        if 'current_proj' not in st.session_state:
            st.session_state['current_proj'] = project_list[0] if project_list else ""
        if st.session_state['current_proj'] not in project_list:
            st.session_state['current_proj'] = project_list[0] if project_list else ""
        
        progress_dict = {}
        if not df_flow.empty:
            for proj in project_list:
                p_df = df_flow[df_flow["프로젝트명"] == proj]
                total_items = len(p_df)
                completed_items = len(p_df[p_df["상태"] == "✅ 완료"])
                pct = int((completed_items / total_items) * 100) if total_items > 0 else 0
                blocks = pct // 10
                bar = "🟩" * blocks + "⬜" * (10 - blocks)
                batt_icon = "🔋" if pct >= 20 else "🪫"
                progress_dict[proj] = f"{proj}  |  {batt_icon} {pct}% ({completed_items}/{total_items}) [{bar}]"

        col_a, col_b = st.columns(2)
        with col_a:
            with st.expander("➕ 새 프로젝트(호기) 시작하기"):
                with st.form("new_proj_form", clear_on_submit=True):
                    new_proj = st.text_input("새 프로젝트명 (예: 4010H #2호기)")
                    source_options = ["기본 템플릿(초기화 상태)"] + project_list
                    source_proj = st.selectbox("어떤 형식을 복사할까요?", source_options, format_func=lambda x: progress_dict.get(x, x))
                    if st.form_submit_button("프로젝트 생성하기") and new_proj and new_proj not in project_list:
                        if source_proj == "기본 템플릿(초기화 상태)": new_df = pd.DataFrame(CS_TEMPLATE)
                        else:
                            new_df = df_flow[df_flow["프로젝트명"] == source_proj].copy()
                            new_df[["상태", "비고", "첨부", "업데이트일"]] = ["⬜ 대기", "", "", ""]
                        new_df["프로젝트명"] = new_proj
                        self.db_flow.save(pd.concat([df_flow, new_df], ignore_index=True), sha_flow, f"Create: {new_proj}")
                        st.session_state['current_proj'] = new_proj
                        st.rerun()

        if project_list:
            sel_col, empty_col, save_col, del_col = st.columns([6, 2, 1, 1])
            default_idx = project_list.index(st.session_state['current_proj']) if project_list else 0
            with sel_col: 
                selected_proj = st.selectbox("📌 프로젝트 선택", project_list, index=default_idx, format_func=lambda x: progress_dict.get(x, x))
                st.session_state['current_proj'] = selected_proj 
            with save_col: 
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                btn_save = st.button("💾 변경 저장", use_container_width=True)
            with del_col: 
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ 삭제", use_container_width=True):
                    st.session_state['delete_target_proj'] = selected_proj
                    st.rerun()

            mask = df_flow["프로젝트명"] == selected_proj
            proj_df = df_flow[mask].copy()

            if st.session_state.get('delete_target_proj') == selected_proj:
                st.error(f"🚨 [{selected_proj}] 프로젝트를 영구 삭제하시겠습니까?")
                if st.button("⚠️ 삭제 확정", type="primary"):
                    self.db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
                    st.session_state['delete_target_proj'] = None
                    st.session_state['current_proj'] = project_list[0] if len(project_list) > 1 else ""
                    st.rerun()
                if st.button("❌ 취소"): st.session_state['delete_target_proj'] = None; st.rerun()
                st.stop() 

            cats = proj_df['대항목'].unique().tolist()
            with st.expander("⚙️ 프로젝트 대항목 관리 (추가/수정/삭제/순서변경)"):
                c1, c2, c3, c4 = st.tabs(["➕ 대항목 추가", "✏️ 이름 수정", "❌ 대항목 삭제", "↕️ 순서 변경"])
                
                with c1:
                    with st.form("add_cat_form", clear_on_submit=True):
                        new_c = st.text_input("새 대항목 이름")
                        if st.form_submit_button("추가하기"):
                            if new_c and new_c not in cats:
                                new_row = pd.DataFrame([{"프로젝트명": selected_proj, "대항목": new_c, "순서": 1, "작업내용": "새 작업 내용 입력", "상태": "⬜ 대기", "비고": "", "첨부": "", "업데이트일": ""}])
                                self.db_flow.save(pd.concat([df_flow, new_row], ignore_index=True), sha_flow, f"Add Cat: {new_c}")
                                st.success(f"'{new_c}' 항목이 추가되었습니다.")
                                st.rerun()

                with c2:
                    with st.form("edit_cat_form", clear_on_submit=True):
                        target_c = st.selectbox("수정할 대항목 선택", cats)
                        rename_c = st.text_input("새로운 이름 입력")
                        if st.form_submit_button("이름 변경"):
                            if rename_c and rename_c not in cats:
                                df_flow.loc[(df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == target_c), "대항목"] = rename_c
                                self.db_flow.save(df_flow, sha_flow, f"Rename Cat: {target_c}")
                                st.success("이름이 변경되었습니다.")
                                st.rerun()

                with c3:
                    with st.form("del_cat_form"):
                        del_c = st.selectbox("삭제할 대항목 선택", cats)
                        st.warning("⚠️ 해당 대항목과 안에 포함된 모든 세부 작업이 영구 삭제됩니다.")
                        if st.form_submit_button("삭제 실행"):
                            df_flow = df_flow[~((df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == del_c))]
                            self.db_flow.save(df_flow, sha_flow, f"Delete Cat: {del_c}")
                            st.success("삭제되었습니다.")
                            st.rerun()

                with c4:
                    st.write("표 안의 **'새 순서'** 숫자를 클릭하여 순서를 변경하고 적용 버튼을 누르세요.")
                    order_df = pd.DataFrame({"대항목": cats, "새 순서": range(1, len(cats)+1)})
                    edited_order = st.data_editor(order_df, hide_index=True, use_container_width=True)
                    if st.button("변경된 순서 적용하기"):
                        edited_order = edited_order.sort_values("새 순서")
                        ordered_cats = edited_order["대항목"].tolist()
                        proj_df['__cat_order__'] = pd.Categorical(proj_df['대항목'], categories=ordered_cats, ordered=True)
                        sorted_proj_df = proj_df.sort_values(['__cat_order__', '순서']).drop(columns=['__cat_order__'])
                        
                        new_df_flow = df_flow[df_flow["프로젝트명"] != selected_proj]
                        new_df_flow = pd.concat([new_df_flow, sorted_proj_df], ignore_index=True)
                        self.db_flow.save(new_df_flow, sha_flow, "Reorder Cats")
                        st.success("순서가 적용되었습니다.")
                        st.rerun()

            total_tasks = len(proj_df); comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
            pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
            st.markdown(f"<div style='font-size:16px; font-weight:bold; color:#4CAF50;'>⚡ 전체 진행도 ({comp_tasks} / {total_tasks})</div>", unsafe_allow_html=True)
            st.progress(pct_float, text=f"{int(pct_float * 100)}% 완료")

            proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
            groups = proj_df.groupby('group_id', sort=False) 
            edited_dfs = []; current_user_stamp = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"

            for group_id, group_df in groups:
                cat = group_df['대항목'].iloc[0]
                display_df = group_df.drop(columns=['group_id']).reset_index(drop=True)
                curr_stats = display_df['상태'].tolist()
                
                cat_total = len(curr_stats)
                cat_comp = curr_stats.count('✅ 완료')
                cnt_str = f"({cat_comp}/{cat_total})"
                
                if '🚨 보류' in curr_stats: tab_title = f"🔴 [보류] {cat} {cnt_str}"
                elif curr_stats and all(s == '✅ 완료' for s in curr_stats): tab_title = f"🟢 [완료] {cat} {cnt_str}"
                elif any(s in ['⏳ 작업중', '✅ 완료'] for s in curr_stats): tab_title = f"🟡 [진행] {cat} {cnt_str}"
                else: tab_title = f"📍 [대기] {cat} {cnt_str}"
                
                with st.expander(tab_title, expanded=False):
                    styled_df = display_df.style.apply(get_row_color, axis=1)
                    edited_cat_df = st.data_editor(
                        styled_df, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"editor_{selected_proj}_{group_id}",
                        column_config={
                            "순서": st.column_config.NumberColumn("No", width="small"), 
                            "작업내용": st.column_config.TextColumn("세부 작업 내용", width="large"), 
                            "상태": st.column_config.SelectboxColumn("상태", options=["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"], width="small"),
                            "비고": st.column_config.TextColumn("비고", width="small"),
                            "첨부": st.column_config.TextColumn("첨부", width="small")
                        }
                    )
                    for idx, new_row in edited_cat_df.iterrows():
                        if new_row['상태'] == "⬜ 대기": edited_cat_df.at[idx, '업데이트일'] = ""
                        else:
                            match = display_df[(display_df['작업내용'] == new_row['작업내용']) & (display_df['상태'] == new_row['상태']) & (display_df['비고'] == new_row['비고'])]
                            if match.empty: edited_cat_df.at[idx, '업데이트일'] = current_user_stamp
                            else: edited_cat_df.at[idx, '업데이트일'] = match.iloc[0]['업데이트일']
                    edited_cat_df["대항목"] = cat; edited_cat_df["프로젝트명"] = selected_proj; edited_cat_df["org_group_id"] = group_id 
                    edited_dfs.append(edited_cat_df)

            if btn_save:
                updated_proj_df = pd.concat(edited_dfs, ignore_index=True)
                if not updated_proj_df.empty:
                    updated_proj_df = updated_proj_df.sort_values(by=['org_group_id', '순서'], kind='stable')
                    updated_proj_df['group_id'] = (updated_proj_df['대항목'] != updated_proj_df['대항목'].shift()).cumsum()
                    updated_proj_df["순서"] = updated_proj_df.groupby('group_id').cumcount() + 1
                    updated_proj_df = updated_proj_df.drop(columns=['group_id', 'org_group_id']).reset_index(drop=True)
                original_projects = df_flow['프로젝트명'].unique().tolist()
                new_df_flow = pd.concat([df_flow[~mask], updated_proj_df], ignore_index=True)
                self.db_flow.save(maintain_project_order(new_df_flow, original_projects), sha_flow, f"Update: {selected_proj}")
                st.success("✅ 저장되었습니다!"); st.rerun()
        else: st.info("프로젝트가 없습니다.")
