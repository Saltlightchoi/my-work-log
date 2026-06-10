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
            .small-btn button { padding: 0px !important; min-height: 38px !important; font-size: 18px !important; margin-top: 28px !important; }
            hr { margin: 5px 0px 10px 0px !important; padding: 0px !important; border-top: 1px solid #ccc; }
            .stSelectbox, .stTextInput, .stDateInput, .stTimeInput { margin-bottom: -15px !important; }
            .tight-box { border: 1.5px solid #d3d9df; padding: 10px 15px 15px 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 5px; margin-bottom: 10px; }
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
        # 1. Jam 작성부 (대제목 삭제, 날짜/시간 상단 배치)
        # ==========================================
        # ▶ Row 1: 발생일자 | 발생시간 | (여백) | 📝 | ✏️ | 🗑️
        r1_c1, r1_c2, r1_c3, r1_b1, r1_b2, r1_b3 = st.columns([1.5, 1.5, 4.5, 0.5, 0.5, 0.5])
        
        with r1_c1: date_val = st.date_input("📅 발생일자", value=datetime.today())
        with r1_c2: time_val = st.time_input("⏰ 발생시간", value="now", step=60) # 1분 단위 타이핑 지원
        with r1_b1: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝", help="작성(저장)", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1_b2: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️", help="수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1_b3: 
            st.markdown("<div class='small-btn'>", unsafe_allow_html=True)
            btn_del = st.button("🗑️", help="삭제", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 2: 장비명 | 모듈 | 알람코드 | 알람명 (한 줄 배치, 크기 조절)
        r2_c1, r2_c2, r2_c3, r2_c4 = st.columns([1, 1, 1.5, 2.5])
        
        with r2_c1: 
            equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # ---------------------------------------------------------
        # ★ 무적의 시트 찾기 로직 + 오류 원인 안내
        # ---------------------------------------------------------
        target_sheet = f"{equip_val}_ErrorList".replace(" ", "").lower()
        actual_sheet_name = None
        df_error_master = pd.DataFrame()
        available_tabs = []
        
        try:
            client = self.db_jam.client
            spreadsheet = client.open_by_key(self.db_jam.spreadsheet_id)
            available_tabs = [ws.title for ws in spreadsheet.worksheets()] # 디버그용: 현재 파일의 탭 목록
            
            for ws in spreadsheet.worksheets():
                if ws.title.replace(" ", "").lower() == target_sheet:
                    actual_sheet_name = ws.title
                    break
            
            if actual_sheet_name:
                db_error = DataManager(self.db_jam.spreadsheet_id, actual_sheet_name)
                df_error_master, _ = db_error.load()
                if not df_error_master.empty:
                    df_error_master.columns = df_error_master.columns.str.strip()
        except Exception:
            pass

        with r2_c2:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique()))
            else:
                module_options = ["(데이터 없음)"]
            selected_module = st.selectbox("📍 모듈", module_options)

        with r2_c3:
            code_options = []
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                    code_options = (filtered_by_module["알람코드"].astype(str).str.strip() + " (" + filtered_by_module["알람명"].astype(str).str.strip() + ")").unique().tolist()
            
            if not code_options:
                code_options = ["(데이터 없음)"]
            selected_code = st.selectbox("🔖 알람코드", code_options)

        with r2_c4:
            auto_alarm_name = ""
            if code_options and selected_code != "(데이터 없음)" and " (" in selected_code:
                try:
                    final_code = selected_code.split(" (")[0].strip()
                    auto_alarm_name = selected_code.split(" (")[1].replace(")", "").strip()
                except:
                    final_code = selected_code
            else:
                final_code = selected_code
                
            final_name = st.text_input("📝 알람명", value=auto_alarm_name)

        # ▶ Row 3: 조치내역 | CIP상태
        r3_c1, r3_c2 = st.columns([5, 1.2])
        with r3_c1:
            action_val = st.text_input("🛠️ 조치내역")
        with r3_c2:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 📝 버튼(작성) 저장 로직
        if btn_write:
            if selected_module != "(데이터 없음)" and selected_code != "(데이터 없음)" and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), "발생시간": time_val.strftime("%H:%M"),
                    "장비명": equip_val, "모듈": selected_module, "알람코드": final_code, "알람명": final_name,
                    "조치내역": action_val, "완료시간": "", "DownTime": "", "CIP상태": cip_val, 
                    "업데이트일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                self.db_jam.save(pd.concat([df_jam, new_data], ignore_index=True).fillna(""))
                st.success("✅ 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다. (마스터 데이터 연동을 확인해 주세요.)")
        
        if btn_edit or btn_del:
            st.info("수정/삭제는 하단 데이터 표에서 행을 직접 클릭하여 키보드(Delete)로 지우거나 수정한 뒤 [저장]을 눌러주세요.")

        st.markdown("</div>", unsafe_allow_html=True)

        # 데이터가 없을 경우 진짜 원인 파악을 위한 디버그 메시지 출력
        if df_error_master.empty:
            st.error(f"🚨 파이썬이 연동된 파일 내에서 '{equip_val}_ErrorList' 탭(시트)을 찾지 못했습니다.")
            st.warning(f"💡 현재 파이썬이 읽고 있는 하단 탭 목록: {available_tabs}")
            st.info("👉 해결책: 구글 드라이브에 별도의 파일을 만들지 마시고, 반드시 위 목록이 있는 기존 마스터 파일 안에 새 시트를 추가해 주세요.")

        # ==========================================
        # 3. 통합 이력 조회 (표 내부 검색/필터 기능 + DownTime 자동 계산)
        # ==========================================
        st.markdown("<hr style='margin-top: 15px !important;'>", unsafe_allow_html=True)
        
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
