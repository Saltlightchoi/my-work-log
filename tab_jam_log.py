import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # 1. 상단 타이틀 메뉴 이동 (기존 유지)
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
        if selected_menu != st.session_state.get('current_menu'):
            st.session_state['current_menu'] = selected_menu; st.rerun()

        st.markdown("<hr style='margin: 5px 0px 15px 0px;'>", unsafe_allow_html=True)
        df_jam, _ = self.db_jam.load()

        # ==========================================
        # 1. Jam 작성 (타이트한 UI)
        # ==========================================
        st.markdown("### ✍️ Jam 작성")
        st.markdown("<div style='border: 1.5px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 20px; background-color: #f9fbfd;'>", unsafe_allow_html=True)

        # ▶ Row 1: 발생일자 | 발생시간 | 장비명 | 모듈 | 알람코드 (한 줄 배치)
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns([1, 1, 1.2, 1.2, 1.5])
        
        with r1_c1: date_val = st.date_input("📅 발생일자")
        with r1_c2: time_val = st.time_input("⏰ 발생시간")
        with r1_c3: equip_val = st.selectbox("⚙️ 장비명", EQUIPMENT_OPTIONS)

        # 동적 에러 마스터 로딩
        sheet_name_for_error = f"{equip_val}_ErrorList"
        try:
            db_error = DataManager(self.db_jam.spreadsheet_id, sheet_name_for_error)
            df_error_master, _ = db_error.load()
        except Exception:
            df_error_master = pd.DataFrame()

        with r1_c4:
            module_options = df_error_master["모듈"].dropna().unique().tolist() if not df_error_master.empty and "모듈" in df_error_master.columns else []
            module_options.append("📝 직접 입력")
            selected_module = st.selectbox("📍 모듈", module_options)
            final_module = st.text_input("모듈 직접 입력", label_visibility="collapsed") if selected_module == "📝 직접 입력" else selected_module

        with r1_c5:
            filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == final_module.strip()] if not df_error_master.empty and final_module and final_module != "📝 직접 입력" else pd.DataFrame()
            code_options = filtered_by_module["알람코드"].dropna().unique().tolist() if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns else []
            code_options.append("📝 직접 입력")
            selected_code = st.selectbox("🔖 알람코드", code_options)
            final_code = st.text_input("코드 직접 입력", label_visibility="collapsed") if selected_code == "📝 직접 입력" else selected_code

        # ▶ Row 2: 알람명 | 조치내역 (넓게) | CIP상태
        r2_c1, r2_c2, r2_c3 = st.columns([1.5, 4, 1.2])
        
        with r2_c1:
            # 알람코드를 고르면 알람명이 자동으로 채워지도록 설정
            auto_alarm_name = ""
            if not filtered_by_module.empty and final_code != "📝 직접 입력":
                match = filtered_by_module[filtered_by_module["알람코드"].astype(str) == final_code]
                if not match.empty and "알람명" in match.columns:
                    auto_alarm_name = match.iloc[0]["알람명"]
            
            final_name = st.text_input("📝 알람명", value=auto_alarm_name)

        with r2_c2:
            action_val = st.text_input("🛠️ 조치내역 (원인 및 해결방법)")
            
        with r2_c3:
            cip_val = st.selectbox("📌 CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # ▶ Row 3: 저장 버튼
        if st.button("💾 Jam 이력 등록하기", type="primary", use_container_width=True):
            if final_module and final_code and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), "발생시간": time_val.strftime("%H:%M"),
                    "장비명": equip_val, "모듈": final_module, "알람코드": final_code, "알람명": final_name,
                    "조치내역": action_val, "완료시간": "", "DownTime": "", "CIP상태": cip_val, 
                    "업데이트일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                self.db_jam.save(pd.concat([df_jam, new_data], ignore_index=True).fillna(""))
                st.success("✅ 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다.")
        st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. 이력 조회 및 수정 (완료시간 입력 시 DownTime 자동 계산)
        # ==========================================
        st.markdown("### 🔍 통합 이력 조회 및 완료 처리")
        st.info("💡 표의 각 **열(Column) 제목(예: 장비명, 알람코드)**을 클릭하면 엑셀처럼 돋보기 아이콘이 나와 **개별 검색 및 드롭다운 체크 필터링**이 가능합니다. \n\n✏️ 빈칸인 **'완료시간'**(예: 15:30)을 표에 직접 입력하고 아래 저장 버튼을 누르면 **DownTime이 자동 계산**됩니다.")

        if not df_jam.empty:
            df_display = df_jam.copy()
            if "발생일자" in df_display.columns:
                df_display = df_display.sort_values(by=["발생일자", "발생시간"], ascending=[False, False]).reset_index(drop=True)
            
            # st.data_editor를 사용하여 표 안에서 직접 엑셀처럼 수정 가능
            edited_df = st.data_editor(
                df_display, 
                use_container_width=True, 
                hide_index=True, 
                num_rows="dynamic",
                column_config={
                    "완료시간": st.column_config.TextColumn("완료시간(HH:MM)", help="예: 14:30 형태로 입력"),
                    "DownTime": st.column_config.TextColumn("DownTime(분)", disabled=True), # 자동계산되므로 비활성화
                    "조치내역": st.column_config.TextColumn("조치내역", width="large")
                }
            )

            # 수정 내용 저장 및 DownTime 계산 로직
            if st.button("💾 표 변경사항 저장 및 DownTime 계산", type="secondary"):
                for idx, row in edited_df.iterrows():
                    start_str = str(row.get("발생시간", "")).strip()
                    end_str = str(row.get("완료시간", "")).strip()
                    
                    # 완료시간이 입력되었고, 형식이 HH:MM일 경우 DownTime 계산
                    if start_str and end_str and ":" in start_str and ":" in end_str:
                        try:
                            t_start = datetime.strptime(start_str, "%H:%M")
                            t_end = datetime.strptime(end_str, "%H:%M")
                            diff_minutes = int((t_end - t_start).total_seconds() / 60)
                            
                            # 자정을 넘긴 경우 (예: 23:00 -> 01:00) 처리
                            if diff_minutes < 0:
                                diff_minutes += 24 * 60
                                
                            edited_df.at[idx, "DownTime"] = str(diff_minutes)
                        except ValueError:
                            pass # 시간 포맷이 안 맞으면 무시
                
                self.db_jam.save(edited_df.fillna(""))
                st.success("✅ 변경사항 및 DownTime이 저장되었습니다!")
                st.rerun()
        else:
            st.warning("등록된 데이터가 없습니다.")
