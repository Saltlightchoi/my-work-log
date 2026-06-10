import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 극한의 여백 압축 및 초밀착 UI CSS
        # ==========================================
        st.markdown("""
            <style>
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
            .small-btn button { padding: 0px !important; min-height: 38px !important; font-size: 18px !important; margin-top: 15px !important; }
            hr { margin: 5px 0px 15px 0px !important; padding: 0px !important; border-top: 1px solid #ccc; }
            h3 { margin-top: 15px !important; margin-bottom: 0px !important; padding-bottom: 0px !important; }
            .stSelectbox, .stTextInput, .stDateInput, .stTimeInput { margin-bottom: -15px !important; }
            </style>
        """, unsafe_allow_html=True)

        # 상단 네비게이션 드롭다운
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
        if selected_menu != st.session_state.get('current_menu'):
            st.session_state['current_menu'] = selected_menu; st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        df_jam, _ = self.db_jam.load()

        # ==========================================
        # 1. 대제목 및 우측 상단 미니 버튼 (공백 제로)
        # ==========================================
        c_title, c_b1, c_b2, c_b3 = st.columns([8.5, 0.5, 0.5, 0.5])
        with c_title: 
            st.markdown("<h3>Jam 이력 관리</h3>", unsafe_allow_html=True)
        with c_b1: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_write = st.button("📝", help="작성", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c_b2: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_edit = st.button("✏️", help="수정", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c_b3: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_del = st.button("🗑️", help="삭제", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. Jam 작성 입력 폼 (한 줄 압축 & 자동완성)
        # ==========================================
        
        # ▶ Row 1: 발생일자 | 발생시간 | 장비명 | 모듈 | 알람코드
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns([1, 1, 1.2, 1.2, 1.5])
        
        with r1_c1: date_val = st.date_input("📅 발생일자", value=datetime.today())
        with r1_c2: time_val = st.time_input("⏰ 발생시간", value="now", step=60) # 시간 클릭 시 현재시간 기준 1분단위 조절
        with r1_c3: equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # ---------------------------------------------------------
        # ★ 무적의 시트 찾기 로직: 공백이나 대소문자가 달라도 무조건 찾습니다.
        # ---------------------------------------------------------
        target_sheet = f"{equip_val}_ErrorList".replace(" ", "").lower()
        actual_sheet_name = None
        df_error_master = pd.DataFrame()
        
        try:
            client = self.db_jam.client
            spreadsheet = client.open_by_key(self.db_jam.spreadsheet_id)
            for ws in spreadsheet.worksheets():
                if ws.title.replace(" ", "").lower() == target_sheet:
                    actual_sheet_name = ws.title
                    break
            
            if actual_sheet_name:
                db_error = DataManager(self.db_jam.spreadsheet_id, actual_sheet_name)
                df_error_master, _ = db_error.load()
                if not df_error_master.empty:
                    df_error_master.columns = df_error_master.columns.str.strip() # 헤더 공백 완벽 제거
        except Exception:
            pass

        with r1_c4:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique()))
            else:
                module_options = ["(데이터 없음)"]
            
            # 여기가 바로 자동완성 드롭다운입니다! (클릭 후 타이핑 시 자동 검색)
            selected_module = st.selectbox("📍 모듈", module_options)

        with r1_c5:
            code_options = []
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                    code_options = sorted(list(filtered_by_module["알람코드"].dropna().astype(str).str.strip().unique()))
            
            if not code_options:
                code_options = ["(데이터 없음)"]
                
            # 34를 치면 34525가 나오는 핵심 자동완성 영역입니다.
            selected_code = st.selectbox("🔖 알람코드", code_options)

        # ▶ Row 2: 알람명 | 조치내역 | CIP상태
        r2_c1, r2_c2, r2_c3 = st.columns([1.5, 4, 1.2])
        
        with r2_c1:
            auto_alarm_name = ""
            if not df_error_master.empty and selected_code != "(데이터 없음)":
                match = df_error_master[df_error_master["알람코드"].astype(str).str.strip() == selected_code]
                if not match.empty and "알람명" in match.columns:
                    auto_alarm_name = match.iloc[0]["알람명"].strip()
            
            final_name = st.text_input("📝 알람명", value=auto_alarm_name)

        with r2_c2:
            action_val = st.text_input("🛠️ 조치내역")
            
        with r2_c3:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 📝 펜 아이콘 버튼(작성) 눌렀을 때의 저장 로직
        if btn_write:
            if selected_module != "(데이터 없음)" and selected_code != "(데이터 없음)" and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), "발생시간": time_val.strftime("%H:%M"),
                    "장비명": equip_val, "모듈": selected_module, "알람코드": selected_code, "알람명": final_name,
                    "조치내역": action_val, "완료시간": "", "DownTime": "", "CIP상태": cip_val, 
                    "업데이트일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                self.db_jam.save(pd.concat([df_jam, new_data], ignore_index=True).fillna(""))
                st.success("✅ 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다. (마스터 데이터가 연결되지 않았습니다.)")
        
        if btn_edit or btn_del:
            st.info("수정/삭제는 하단 데이터 표에서 행을 직접 클릭하여 키보드(Delete)로 지우거나 수정한 뒤 [저장]을 눌러주세요.")

        if df_error_master.empty:
            st.error(f"🚨 구글 시트에서 '{equip_val}_ErrorList' 데이터를 불러오는 데 실패했습니다. 시트 이름이나 권한, 혹은 캐시를 확인해 주세요.")

        # ==========================================
        # 3. 통합 이력 조회 (표 내부 검색/필터 기능 + DownTime 자동 계산)
        # ==========================================
        st.markdown("<hr style='margin-top: 30px !important;'>", unsafe_allow_html=True)
        
        if not df_jam.empty:
            df_display = df_jam.copy()
            if "발생일자" in df_display.columns:
                df_display = df_display.sort_values(by=["발생일자", "발생시간"], ascending=[False, False]).reset_index(drop=True)
            
            edited_df = st.data_editor(
                df_display, 
                use_container_width=True, 
                hide_index=True, 
                num_rows="dynamic",
                column_config={
                    "완료시간": st.column_config.TextColumn("완료시간(HH:MM)"),
                    "DownTime": st.column_config.TextColumn("DownTime(분)", disabled=True),
                    "조치내역": st.column_config.TextColumn("조치내역", width="large")
                }
            )

            if st.button("💾 표 변경사항 저장 (완료시간 적용 및 DownTime 계산)", type="secondary"):
                for idx, row in edited_df.iterrows():
                    start_str = str(row.get("발생시간", "")).strip()
                    end_str = str(row.get("완료시간", "")).strip()
                    
                    if start_str and end_str and ":" in start_str and ":" in end_str:
                        try:
                            t_start = datetime.strptime(start_str, "%H:%M")
                            t_end = datetime.strptime(end_str, "%H:%M")
                            diff_minutes = int((t_end - t_start).total_seconds() / 60)
                            if diff_minutes < 0: diff_minutes += 24 * 60
                            edited_df.at[idx, "DownTime"] = str(diff_minutes)
                        except ValueError:
                            pass 
                
                self.db_jam.save(edited_df.fillna(""))
                st.success("✅ 변경사항 및 DownTime이 저장되었습니다!")
                st.rerun()
        else:
            st.warning("등록된 데이터가 없습니다.")
