import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import EQUIPMENT_OPTIONS

class WorkLogTab:
    def __init__(self, db_log):
        self.db_log = db_log

    def render(self):
        # ==========================================
        # 1. 데이터 로드 및 전처리
        # ==========================================
        df_log, _ = self.db_log.load()
        
        if not df_log.empty and '날짜' in df_log.columns:
            df_log['날짜_dt'] = pd.to_datetime(df_log['날짜'], errors='coerce')
            df_log['날짜'] = df_log['날짜_dt'].dt.date.astype(str)
            df_log = df_log.sort_values(by='날짜_dt', ascending=False).reset_index(drop=True)

        # ==========================================
        # 2. 사이드바: 일지 작성/수정/삭제
        # ==========================================
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📝 일지 작성/수정/삭제")
        mode = st.sidebar.selectbox("기능 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
        
        if mode == "➕ 작성":
            with st.sidebar.form("add_log", clear_on_submit=True):
                d = st.date_input("날짜", datetime.today())
                e = st.selectbox("장비", EQUIPMENT_OPTIONS)
                c = st.text_area("업무 내용", height=300)
                a1 = st.text_input("첨부 1 (G-Drive 링크)")
                a2 = st.text_input("첨부 2 (G-Drive 링크)") 
                if st.form_submit_button("저장하기"):
                    user_name = st.session_state.get('user_name', '본인')
                    new_row = pd.DataFrame([{"날짜": str(d), "장비": e, "작성자": user_name, "업무내용": c, "비고": a2.strip(), "첨부": a1.strip()}])
                    save_df = pd.concat([df_log.drop(columns=['날짜_dt'], errors='ignore'), new_row], ignore_index=True)
                    self.db_log.save(save_df)
                    st.cache_data.clear() 
                    st.rerun()

        elif mode == "✏️ 수정" and not df_log.empty:
            idx = st.sidebar.selectbox(
                "수정 대상", 
                df_log.index, 
                format_func=lambda x: f"{df_log.loc[x, '날짜']} | 👤{df_log.loc[x, '작성자']} | {str(df_log.loc[x, '업무내용'])[:10]}..."
            )
            with st.sidebar.form("edit_log"):
                try: e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[idx, '날짜']))
                except: e_date = st.date_input("날짜 수정", datetime.today())
                
                current_equip = df_log.loc[idx, '장비'] if '장비' in df_log.columns and pd.notna(df_log.loc[idx, '장비']) else EQUIPMENT_OPTIONS[0]
                if current_equip not in EQUIPMENT_OPTIONS: current_equip = EQUIPMENT_OPTIONS[0]
                e_equip = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(current_equip))
                
                val_author = df_log.loc[idx, '작성자'] if '작성자' in df_log.columns else ""
                e_author = st.text_input("작성자 확인 및 수정", value="" if pd.isna(val_author) else str(val_author))
                e_content = st.text_area("내용 수정", value=str(df_log.loc[idx, '업무내용']), height=300)
                
                val_attach1 = df_log.loc[idx, '첨부'] if '첨부' in df_log.columns else ""
                e_attach1 = st.text_input("첨부 1 수정 (G-Drive 링크)", value="" if pd.isna(val_attach1) else str(val_attach1))
                
                val_attach2 = df_log.loc[idx, '비고'] if '비고' in df_log.columns else ""
                e_attach2 = st.text_input("첨부 2 수정 (G-Drive 링크)", value="" if pd.isna(val_attach2) else str(val_attach2))
                
                if st.form_submit_button("수정 완료"):
                    df_log.loc[idx, ['날짜', '장비', '작성자', '업무내용', '비고', '첨부']] = [str(e_date), e_equip, e_author, e_content, e_attach2.strip(), e_attach1.strip()]
                    save_df = df_log.drop(columns=['날짜_dt'], errors='ignore')
                    self.db_log.save(save_df)
                    st.cache_data.clear() 
                    st.rerun()

        elif mode == "❌ 삭제" and not df_log.empty:
            idx = st.sidebar.selectbox(
                "삭제 대상 선택", 
                df_log.index, 
                format_func=lambda x: f"{df_log.loc[x, '날짜']} | 👤{df_log.loc[x, '작성자']} | {str(df_log.loc[x, '업무내용'])[:10]}"
            )
            st.sidebar.warning(f"내용: {str(df_log.loc[idx, '업무내용'])[:50]}...")
            if st.sidebar.button("🗑️ 최종 삭제 (복구 불가)", type="primary"):
                save_df = df_log.drop(idx).drop(columns=['날짜_dt'], errors='ignore')
                self.db_log.save(save_df)
                st.cache_data.clear() 
                st.rerun()

        # ==========================================
        # 3. 메인 화면: 타이틀 옆에 드롭다운 메뉴 붙이기
        # ==========================================
        col_title, col_empty, col_menu, col_excel = st.columns([4.5, 2.5, 2, 1])
        with col_title:
            st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
        with col_empty:
            pass # 빈 공간으로 밀어내기
        with col_menu:
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            selected_menu = st.selectbox(
                "메뉴",
                ["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"],
                index=["📝 업무일지", "✅ 장비 제작 Flow", "📊 장비가동데이터", "🛠️ ECN & STN"].index(st.session_state['current_menu']),
                key="menu_worklog",
                label_visibility="collapsed"
            )
            if selected_menu != st.session_state['current_menu']:
                st.session_state['current_menu'] = selected_menu
                st.rerun()
        with col_excel:
            export_df = df_log.drop(columns=['날짜_dt'], errors='ignore') if not df_log.empty else df_log
            export_df = export_df.rename(columns={"비고": "첨부 2", "첨부": "첨부 1"})
            csv_data = export_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(label="📥 엑셀 다운로드", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

        st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)

        # ==========================================
        # 4. 필터링 UI
        # ==========================================
        filter_col1, filter_col2, filter_col3 = st.columns([3, 3, 4])
        with filter_col1:
            date_range = st.date_input("📅 검색 날짜 범위", value=(datetime.now() - timedelta(weeks=2), datetime.now()))
        with filter_col2:
            equip_options = df_log['장비'].dropna().unique().tolist() if '장비' in df_log.columns else []
            equip_filter = st.multiselect("📌 장비 선택", options=equip_options)
        with filter_col3:
            keyword = st.text_input("🔍 내용/작성자 검색", placeholder="검색어를 입력하세요...")

        st.markdown("<br>", unsafe_allow_html=True)

        # ==========================================
        # 5. 데이터 필터링 적용 및 화면 출력
        # ==========================================
        filtered_df = df_log.copy()
        
        if not filtered_df.empty and '날짜_dt' in filtered_df.columns:
            if isinstance(date_range, tuple) and len(date_range) == 2:
                mask = (filtered_df['날짜_dt'].dt.date >= date_range[0]) & (filtered_df['날짜_dt'].dt.date <= date_range[1])
                filtered_df = filtered_df.loc[mask]

        if equip_filter:
            filtered_df = filtered_df[filtered_df['장비'].isin(equip_filter)]
            
        if keyword:
            filtered_df = filtered_df[
                filtered_df['업무내용'].astype(str).str.contains(keyword, na=False, case=False) |
                filtered_df['작성자'].astype(str).str.contains(keyword, na=False, case=False)
            ]

        if '날짜_dt' in filtered_df.columns:
            filtered_df = filtered_df.drop(columns=['날짜_dt'])

        if '첨부' in filtered_df.columns:
            filtered_df['첨부'] = filtered_df['첨부'].apply(lambda x: x if pd.notna(x) and str(x).strip() != "" else None)
        if '비고' in filtered_df.columns:
            filtered_df['비고'] = filtered_df['비고'].apply(lambda x: x if pd.notna(x) and str(x).strip() != "" else None)

        display_order = ["날짜", "장비", "작성자", "업무내용", "첨부", "비고"]
        actual_order = [col for col in display_order if col in filtered_df.columns]

        st.dataframe(
            filtered_df, 
            use_container_width=True, 
            hide_index=True, 
            column_order=actual_order,
            column_config={
                "업무내용": st.column_config.TextColumn("업무내용", width="large"),
                "첨부": st.column_config.LinkColumn("첨부 1", display_text="🔗 열기 1", width="small"),
                "비고": st.column_config.LinkColumn("첨부 2", display_text="🔗 열기 2", width="small")
            }
        )
