import streamlit as st
import pandas as pd
from datetime import datetime
from config import CS_TEMPLATE, maintain_project_order, get_row_color, EQUIPMENT_OPTIONS

class CSCheckSheetTab:
    def __init__(self, db_flow):
        self.db_flow = db_flow

    def render(self):
        df_flow, sha_flow = self.db_flow.load()
        
        # 세션 초기화: 상세 보기를 위한 변수
        if 'view_project_detail' not in st.session_state:
            st.session_state['view_project_detail'] = None

        project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []

        # ==========================================
        # 뷰 1: 상세 작업 화면 (특정 프로젝트 클릭 시)
        # ==========================================
        if st.session_state['view_project_detail'] and st.session_state['view_project_detail'] in project_list:
            selected_proj = st.session_state['view_project_detail']
            
            # 상단 네비게이션
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

            # 제어부 (저장 / 삭제)
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
                    self.db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
                    st.session_state['delete_target_proj'] = None
                    st.session_state['view_project_detail'] = None # 삭제 후 메인으로
                    st.rerun()
                if st.button("❌ 취소"): 
                    st.session_state['delete_target_proj'] = None
                    st.rerun()
                st.stop() 

            # 대항목 관리
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

            # 진행률 표시
            total_tasks = len(proj_df); comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
            pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
            st.markdown(f"<div style='font-size:16px; font-weight:bold; color:#4CAF50;'>⚡ 해당 호기 진행도 ({comp_tasks} / {total_tasks})</div>", unsafe_allow_html=True)
            st.progress(pct_float, text=f"{int(pct_float * 100)}% 완료")

            # 에디터 테이블 출력
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

            # 저장 로직
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

        # ==========================================
        # 뷰 2: 전체 현황판 메인 화면 (기본 뷰)
        # ==========================================
        else:
            st.markdown("<div class='main-title'>✅ 장비 제작 Flow 전체 현황판</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

            # 새 프로젝트 추가 버튼
            with st.expander("➕ 새 장비(호기) 제작 시작하기"):
                with st.form("new_proj_form", clear_on_submit=True):
                    new_proj = st.text_input("새 장비명 (예: 4010H #2호기)")
                    source_options = ["기본 템플릿(초기화 상태)"] + project_list
                    source_proj = st.selectbox("어떤 형식(기존 호기)을 복사할까요?", source_options)
                    if st.form_submit_button("프로젝트 생성하기") and new_proj and new_proj not in project_list:
                        if source_proj == "기본 템플릿(초기화 상태)": new_df = pd.DataFrame(CS_TEMPLATE)
                        else:
                            new_df = df_flow[df_flow["프로젝트명"] == source_proj].copy()
                            new_df[["상태", "비고", "첨부", "업데이트일"]] = ["⬜ 대기", "", "", ""]
                        new_df["프로젝트명"] = new_proj
                        self.db_flow.save(pd.concat([df_flow, new_df], ignore_index=True), sha_flow, f"Create: {new_proj}")
                        st.session_state['view_project_detail'] = new_proj # 생성 후 바로 진입
                        st.rerun()

            # ★ 필터 UI 추가 (우측 정렬 배치)
            filter_col1, empty_col, filter_col2 = st.columns([2.5, 3, 4.5])
            with filter_col1:
                model_filter = st.selectbox("📌 모델별 필터", ["전체"] + EQUIPMENT_OPTIONS)
            with filter_col2:
                st.markdown("<div style='font-size: 14px; color: #333; margin-bottom: 5px; font-weight: bold;'>📌 진행 상태 필터</div>", unsafe_allow_html=True)
                sc1, sc2, sc3 = st.columns(3)
                show_todo = sc1.checkbox("📍 예정(대기)", value=True)
                show_prog = sc2.checkbox("🏃‍♂️ 진행중", value=True)
                show_done = sc3.checkbox("✅ 완료", value=True)
                
            st.markdown("<hr style='margin-top: 15px; margin-bottom: 25px;'>", unsafe_allow_html=True)

            if not project_list:
                st.info("현재 진행 중인 장비 제작 Flow가 없습니다. 위에서 새 장비를 추가해 주세요.")
                return
            
            # --- 장비 진행률 사전 계산, 필터링 및 분류 ---
            todo_projects = []
            prog_projects = []
            completed_projects = []
            
            for proj in project_list:
                # 1. 모델 필터 적용
                if model_filter != "전체" and model_filter.lower() not in proj.lower():
                    continue

                p_df = df_flow[df_flow["프로젝트명"] == proj]
                total_items = len(p_df)
                completed_items = len(p_df[p_df["상태"] == "✅ 완료"])
                pct = int((completed_items / total_items) * 100) if total_items > 0 else 0
                
                # 상태 확인
                if pct == 100: status_cat = "완료"
                elif pct > 0: status_cat = "진행중"
                else: status_cat = "대기"

                # 2. 상태 필터 적용 (선택된 항목만 각 리스트에 넣음)
                proj_data = {"name": proj, "total": total_items, "completed": completed_items, "pct": pct}
                
                if status_cat == "완료" and show_done:
                    completed_projects.append(proj_data)
                elif status_cat == "진행중" and show_prog:
                    prog_projects.append(proj_data)
                elif status_cat == "대기" and show_todo:
                    todo_projects.append(proj_data)

            # 카드 렌더링 함수
            def render_project_cards(proj_data_list):
                cols = st.columns(3)
                for idx, p_data in enumerate(proj_data_list):
                    proj = p_data["name"]
                    total_items = p_data["total"]
                    completed_items = p_data["completed"]
                    pct = p_data["pct"]
                    
                    # 배터리 및 게이지 블록 계산
                    blocks = pct // 10
                    bar = "🟩" * blocks + "⬜" * (10 - blocks)
                    batt_icon = "🔋" if pct >= 20 else "🪫"
                    
                    # 상태별 색상
                    if pct == 100: color, bg = "#4CAF50", "#e8f5e9" # 초록 (완료)
                    elif pct > 0: color, bg = "#2196F3", "#e3f2fd"  # 파랑 (진행중)
                    else: color, bg = "#9e9e9e", "#f5f5f5"          # 회색 (대기)

                    with cols[idx % 3]:
                        # 예쁜 카드 UI 렌더링
                        st.markdown(f"""
                            <div style="background-color: {bg}; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 6px solid {color}; margin-bottom: 15px;">
                                <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 5px;">{proj}</div>
                                <div style="font-size: 14px; color: #666; margin-bottom: 10px;">작업 현황: {completed_items} / {total_items} 건</div>
                                <div style="font-size: 26px; font-weight: bold; color: {color}; margin-bottom: 5px;">{pct}%</div>
                                <div style="font-size: 14px; letter-spacing: 1.5px; color: #333;">{batt_icon} [{bar}]</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 상세 보기 버튼
                        if st.button(f"🔍 [{proj}] 상세 작업 및 체크하기", key=f"btn_{proj}", use_container_width=True):
                            st.session_state['view_project_detail'] = proj
                            st.rerun()
                        st.markdown("<br>", unsafe_allow_html=True)

            # 3. 화면 출력 (조건에 맞는 데이터가 있을 때만 껍데기 제목 출력!)
            has_data = False
            
            if todo_projects:
                st.markdown("### 📍 예정(대기) 장비 목록")
                render_project_cards(todo_projects)
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                has_data = True
                
            if prog_projects:
                st.markdown("### 🏃‍♂️ 진행 중인 장비 목록")
                render_project_cards(prog_projects)
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 25px; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)
                has_data = True
                
            if completed_projects:
                st.markdown("### ✅ 제작 완료된 장비 목록")
                render_project_cards(completed_projects)
                has_data = True
                
            # 체크를 다 끄거나 검색 조건에 아예 안 맞을 때만 이 문구 하나 출력
            if not has_data:
                st.info("조건에 맞는 장비가 없습니다. 필터 옵션을 확인해 주세요.")
