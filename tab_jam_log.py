import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 군더더기 없는 깔끔한 UI를 위한 CSS
        # ==========================================
        st.markdown("""
            <style>
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
            .action-btn button { min-height: 38px !important; margin-top: 28px !important; padding: 0px 10px !important; font-size: 14px !important; }
            hr { margin: 5px 0px 15px 0px !important; padding: 0px !important; border-top: 1px solid #ccc; }
            .tight-box { border: 1px solid #d3d9df; padding: 15px 20px; border-radius: 8px; background-color: #f8fafc; margin-bottom: 15px; }
            </style>
        """, unsafe_allow_html=True)

        # 상단 네비게이션 드롭다운 (탭 이름)
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
        # 1. 발생일시 및 버튼 (대제목 위치로 이동)
        # ==========================================
        r0_c1, r0_c2, r0_spacer, r0_b1, r0_b2, r0_b3 = st.columns([1.5, 1.5, 4.5, 1, 1, 1])
        
        with r0_c1: date_val = st.date_input("📅 발생일자", value=datetime.today())
        with r0_c2: time_val = st.time_input("⏰ 발생시간", value="now", step=60) # 1분 단위 타이핑 지원
        
        with r0_b1: 
            st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝 저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r0_b2: 
            st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️ 수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r0_b3: 
            st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
            btn_del = st.button("🗑️ 삭제", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. 내역 작성 박스 (4항목 한 줄 압축 & 알람명 중심 검색)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1: 장비명 | 모듈 | 알람명(드롭다운 검색) | 알람코드(자동입력)
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns([1.2, 1.2, 3, 1.2]) # 알람명을 길게, 코드를 짧게 설정
        
        with r1_c1: 
            equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # 구글 시트 마스터 데이터 연동 로직
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
                    df_error_master.columns = df_error_master.columns.str.strip()
        except Exception:
            pass

        with r1_c2:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique()))
            else:
                module_options = ["(데이터 없음)"]
            selected_module = st.selectbox("📍 모듈", module_options)

        with r1_c3:
            name_options = []
            filtered_by_module = pd.DataFrame()
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람명" in filtered_by_module.columns:
                    # 알람명만 리스트로 쫙 뽑아줍니다.
                    name_options = sorted(list(filtered_by_module["알람명"].dropna().astype(str).str.strip().unique()))
            
            if not name_options:
                name_options = ["(데이터 없음)"]
                
            # ★ 핵심: 알람명을 타이핑해서 검색하는 자동완성 드롭다운
            selected_alarm_name = st.selectbox("📝 알람명 (타이핑 검색)", name_options)

        with r1_c4:
            # 알람명을 고르면 마스터 시트에서 해당 알람코드를 찾아옵니다.
            auto_code = ""
            if selected_alarm_name != "(데이터 없음)" and not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                match = filtered_by_module[filtered_by_module["알람명"].astype(str).str.strip() == selected_alarm_name]
                if not match.empty:
                    auto_code = match.iloc[0]["알람코드"]
            
            # 딱 알람코드만 깔끔하게 표시 및 직접 수정도 가능하게 처리
            final_code = st.text_input("🔖 알람코드", value=auto_code)

        # ▶ Row 2: 조치내역 | CIP상태
        r2_c1, r2_c2 = st.columns([5, 1.5])
        with r2_c1:
            action_val = st.text_input("🛠️ 조치내역")
        with r2_c2:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        st.markdown("</div>", unsafe_allow_html=True)

        # 📝 저장 버튼 로직
        if btn_write:
            if selected_module != "(데이터 없음)" and final_code and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), "발생시간": time_val.strftime("%H:%M"),
                    "장비명": equip_val, "모듈": selected_module, "알람코드": final_code, "알람명": selected_alarm_name,
                    "조치내역": action_val, "완료시간": "", "DownTime": "", "CIP상태": cip_val, 
                    "업데이트일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                self.db_jam.save(pd.concat([df_jam, new_data], ignore_index=True).fillna(""))
                st.success("✅ 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다. (마스터 데이터를 확인해 주세요.)")
        
        if btn_edit or btn_del:
            st.info("💡 수정/삭제는 하단 데이터 표 안의 항목을 클릭하여 수정하거나, 행 좌측을 선택해 키보드(Delete)로 지운 뒤 [표 변경사항 저장]을 누르시면 됩니다.")

        # ==========================================
        # 3. 통합 이력 조회 (표 내부 검색/필터 기능 + DownTime 자동 계산)
        # ==========================================
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
            st.info("등록된 데이터가 없습니다.")
