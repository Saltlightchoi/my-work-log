import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 극한의 여백 압축 및 미니 버튼용 CSS
        # ==========================================
        st.markdown("""
            <style>
            .small-btn button { padding: 0px !important; min-height: 38px !important; font-size: 18px !important; margin-top: 2px !important; }
            .tight-box { border: 1.5px solid #d3d9df; padding: 15px; border-radius: 8px; background-color: #f8fafc; margin-top: 0px; margin-bottom: 10px; }
            hr { margin: 5px 0px 10px 0px !important; padding: 0px !important; }
            h3 { margin-top: 0px !important; margin-bottom: 5px !important; padding-bottom: 0px !important; }
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
        # 1. 대제목 및 우측 상단 미니 버튼 (불필요한 공백/글자 제거)
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
        # 2. Jam 작성 입력 폼 (타이트한 UI)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1: 발생일자 | 발생시간 | 장비명 | 모듈 | 알람코드
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns([1, 1, 1.2, 1.2, 2])
        
        with r1_c1: date_val = st.date_input("📅 발생일자", value=datetime.today())
        with r1_c2: time_val = st.time_input("⏰ 발생시간", value="now", step=60) # 1분 단위 타이핑 지원
        with r1_c3: equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # 동적 에러 마스터 로딩 (선택한 장비명 기준)
        sheet_name_for_error = f"{equip_val}_ErrorList"
        try:
            db_error = DataManager(self.db_jam.spreadsheet_id, sheet_name_for_error)
            df_error_master, _ = db_error.load()
            if not df_error_master.empty:
                df_error_master.columns = df_error_master.columns.str.strip() # 공백 제거 안전장치
        except Exception:
            df_error_master = pd.DataFrame()

        with r1_c4:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique()))
                selected_module = st.selectbox("📍 모듈 (타이핑 검색)", module_options)
            else:
                selected_module = st.text_input("📍 모듈 (직접입력)")

        with r1_c5:
            code_options = []
            if not df_error_master.empty and selected_module:
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module.strip()]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns and "알람명" in filtered_by_module.columns:
                    # 타이핑 검색을 위해 "34525 (로봇 슬립)" 형태로 리스트 병합
                    code_options = (filtered_by_module["알람코드"].astype(str).str.strip() + " (" + filtered_by_module["알람명"].astype(str).str.strip() + ")").unique().tolist()
            
            if code_options:
                selected_alarm = st.selectbox("🔖 알람코드 (숫자 타이핑 시 자동 필터)", code_options)
            else:
                selected_alarm = st.text_input("🔖 알람코드 (직접입력)")

        # ▶ Row 2: 알람명 | 조치내역 | CIP상태
        r2_c1, r2_c2, r2_c3 = st.columns([1.5, 4, 1.2])
        
        with r2_c1:
            # 알람코드 드롭다운에서 선택 시 괄호 내용을 분리하여 알람명에 자동 삽입
            if code_options and " (" in selected_alarm:
                try:
                    final_code = selected_alarm.split(" (")[0].strip()
                    auto_alarm_name = selected_alarm.split(" (")[1].replace(")", "").strip()
                except IndexError:
                    final_code = selected_alarm
                    auto_alarm_name = ""
            else:
                final_code = selected_alarm
                auto_alarm_name = ""
                
            final_name = st.text_input("📝 알람명", value=auto_alarm_name)

        with r2_c2:
            action_val = st.text_input("🛠️ 조치내역")
            
        with r2_c3:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 📝 펜 아이콘 버튼(작성) 눌렀을 때의 저장 로직
        if btn_write:
            if selected_module and final_code and action_val:
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
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다.")
        
        if btn_edit or btn_del:
            st.info("수정 및 삭제는 아래 데이터 표에서 항목을 직접 수정하거나, 행을 선택해 키보드의 Delete 키로 지운 뒤 [표 변경사항 저장]을 눌러주세요.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 3. 통합 이력 조회 (DownTime 자동 계산)
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
            st.warning("등록된 데이터가 없습니다.")
