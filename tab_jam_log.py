import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # UI 여백 강제 축소 및 미니 버튼용 커스텀 CSS
        st.markdown("""
            <style>
            .small-btn button { padding: 0px 5px !important; min-height: 35px !important; }
            .tight-box { border: 1.5px solid #d3d9df; padding: 10px 15px; border-radius: 8px; background-color: #f8fafc; margin-bottom: 10px; }
            hr { margin: 10px 0px !important; }
            </style>
        """, unsafe_allow_html=True)

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
        # 1. Jam 작성 (타이트한 UI & 미니 버튼)
        # ==========================================
        c_title, c_b1, c_b2, c_b3 = st.columns([7, 0.6, 0.6, 0.6])
        with c_title: st.markdown("<h4 style='margin:0;'>✍️ Jam 작성</h4>", unsafe_allow_html=True)
        with c_b1: st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_write = st.button("📝", help="Jam 이력 등록", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c_b2: st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_edit = st.button("✏️", help="선택 항목 수정 (준비중)", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)
        with c_b3: st.markdown("<div class='small-btn'>", unsafe_allow_html=True); btn_del = st.button("🗑️", help="선택 항목 삭제 (준비중)", use_container_width=True); st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1: 발생일자 | 발생시간 | 장비명 | 모듈 | 알람코드
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns([1, 1, 1.2, 1.2, 2])
        
        with r1_c1: date_val = st.date_input("📅 발생일자", value=datetime.today())
        with r1_c2: time_val = st.time_input("⏰ 발생시간", value="now", step=60) # step=60으로 1분 단위 설정 및 15분 제한 해제
        with r1_c3: equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # 동적 에러 마스터 로딩
        sheet_name_for_error = f"{equip_val}_ErrorList"
        try:
            db_error = DataManager(self.db_jam.spreadsheet_id, sheet_name_for_error)
            df_error_master, _ = db_error.load()
        except Exception:
            df_error_master = pd.DataFrame()

        with r1_c4:
            # 직접입력 제거, 순수 드롭다운 (타이핑 가능)
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).unique()))
            else:
                module_options = ["데이터 없음"]
            selected_module = st.selectbox("📍 모듈", module_options)

        with r1_c5:
            if not df_error_master.empty and selected_module != "데이터 없음":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module.strip()]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                    # 타이핑 검색을 위해 코드와 이름을 합침
                    code_options = (filtered_by_module["알람코드"].astype(str) + " (" + filtered_by_module["알람명"].astype(str) + ")").unique().tolist()
                else:
                    code_options = ["데이터 없음"]
            else:
                code_options = ["데이터 없음"]
                
            selected_alarm = st.selectbox("🔖 알람코드 (검색: 번호 타이핑)", code_options)

        # ▶ Row 2: 알람명 | 조치내역 | CIP상태
        r2_c1, r2_c2, r2_c3 = st.columns([1.5, 4, 1.2])
        
        with r2_c1:
            # 알람코드 선택 시 자동 분리 추출
            if selected_alarm != "데이터 없음":
                try:
                    final_code = selected_alarm.split(" (")[0].strip()
                    auto_alarm_name = selected_alarm.split(" (")[1].replace(")", "").strip()
                except IndexError:
                    final_code = selected_alarm
                    auto_alarm_name = ""
            else:
                final_code, auto_alarm_name = "", ""
                
            final_name = st.text_input("📝 알람명", value=auto_alarm_name)

        with r2_c2:
            action_val = st.text_input("🛠️ 조치내역")
            
        with r2_c3:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 상단 📝 버튼을 눌렀을 때의 저장 로직
        if btn_write:
            if selected_module != "데이터 없음" and final_code and action_val:
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
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다. (마스터 데이터가 없는 경우 구글 시트 확인)")
        st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. 이력 조회 (완료시간 입력 시 DownTime 자동 계산)
        # ==========================================
        st.markdown("### 🔍 통합 이력 조회")
        st.info("💡 **각 열 제목(장비명, 알람코드 등)** 클릭 시 나오는 아이콘으로 필터링/검색이 가능합니다. 빈칸인 **'완료시간'**(예: 15:30)을 표에 직접 입력하고 저장하면 **DownTime이 자동 계산**됩니다.")

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

            if st.button("💾 표 변경사항 저장", type="secondary"):
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
