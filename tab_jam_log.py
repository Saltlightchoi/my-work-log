import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 0. 타이틀 드롭다운 메뉴 (화면 상단 네비게이션)
        # ==========================================
        menu_options = ["📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)","🚨 Jam & 트러블슈팅 이력"]
        
        selected_menu = st.selectbox(
            "메뉴",
            menu_options,
            index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")),
            key="menu_jam_log",
            label_visibility="collapsed"
        )
        
        if selected_menu != st.session_state.get('current_menu'):
            st.session_state['current_menu'] = selected_menu
            st.rerun()

        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
        
        # 데이터 로드
        df_jam, _ = self.db_jam.load()

        # ==========================================
        # 1. 새로운 Jam 이력 입력부
        # ==========================================
        st.markdown("### ➕ 새로운 Jam/장애 이력 등록")
        st.markdown("<div style='border: 1px solid #ddd; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("발생 일자")
        with c2:
            equip_val = st.selectbox("장비명", EQUIPMENT_OPTIONS)

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # 동적 에러 마스터 로딩
        sheet_name_for_error = f"{equip_val}_ErrorList"
        try:
            db_error = DataManager(self.db_jam.spreadsheet_id, sheet_name_for_error)
            df_error_master, _ = db_error.load()
        except Exception:
            df_error_master = pd.DataFrame()

        c3, c4 = st.columns(2)

        with c3:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = df_error_master["모듈"].dropna().unique().tolist()
            else:
                module_options = []
            
            module_options.append("📝 직접 입력")
            selected_module = st.selectbox("모듈(위치) 선택", module_options)
            
            if selected_module == "📝 직접 입력":
                final_module = st.text_input("모듈명을 직접 입력하세요", key="manual_mod")
            else:
                final_module = selected_module

        with c4:
            filtered_by_module = pd.DataFrame()
            if not df_error_master.empty and final_module and final_module != "📝 직접 입력":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == final_module.strip()]

            if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns and "알람명" in filtered_by_module.columns:
                alarm_list = (filtered_by_module["알람코드"].astype(str) + " (" + filtered_by_module["알람명"].astype(str) + ")").unique().tolist()
            else:
                alarm_list = []
                
            alarm_list.append("📝 직접 입력")

            selected_alarm = st.selectbox("알람 코드 및 알람명 (타이핑하여 자동검색)", alarm_list)

            if selected_alarm == "📝 직접 입력":
                col_a, col_b = st.columns(2)
                with col_a: final_alarm_code = st.text_input("알람 코드 (예: Err-999)", key="manual_code")
                with col_b: final_issue = st.text_input("알람명 입력", key="manual_issue")
            else:
                try:
                    final_alarm_code = selected_alarm.split(" (")[0].strip()
                    final_issue = selected_alarm.split(" (")[1].replace(")", "").strip()
                except IndexError:
                    final_alarm_code = selected_alarm
                    final_issue = selected_alarm

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        action_val = st.text_input("🛠️ 조치 내역 (자세히 적어주세요)")

        c5, c6, c7 = st.columns(3)
        with c5:
            result_val = st.selectbox("조치 결과", ["✅ 완료(양호)", "👀 모니터링 중", "⚠️ 임시조치(재발가능)"])
        with c6:
            downtime_val = st.number_input("DownTime (정지 시간/분)", min_value=0)
        with c7:
            cip_val = st.selectbox("CIP(개선) 상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        if st.button("💾 Jam 이력 저장", type="primary", use_container_width=True):
            if final_module and final_alarm_code and final_issue and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), 
                    "장비명": equip_val,
                    "모듈(위치)": final_module, 
                    "알람코드": final_alarm_code, 
                    "발생현상": final_issue, 
                    "조치내역": action_val, 
                    "조치결과": result_val, 
                    "DownTime(분)": downtime_val, 
                    "CIP상태": cip_val
                }])
                
                combined_df = pd.concat([df_jam, new_data], ignore_index=True).fillna("")
                self.db_jam.save(combined_df)
                st.success("✅ 조치 이력이 성공적으로 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 알람명, 조치내역은 필수 입력 항목입니다. 빠진 곳이 없는지 확인해 주세요.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. 과거 이력 검색 및 데이터 확인
        # ==========================================
        st.markdown("### 🔍 과거 트러블슈팅 이력 통합 검색")
        
        c8, c9 = st.columns([1, 3])
        with c8:
            filter_equip = st.selectbox("장비명 필터", ["전체"] + EQUIPMENT_OPTIONS, key="filter_equip")
        with c9:
            search_kw = st.text_input("검색어 입력 (알람코드, 알람명, 조치내역 등 통합 검색)", placeholder="예: Err-402, 슬립, 로봇")
        
        display_df = df_jam.copy()
        
        if not display_df.empty:
            if filter_equip != "전체":
                display_df = display_df[display_df["장비명"] == filter_equip]
                
            if search_kw:
                mask = display_df.apply(lambda row: row.astype(str).str.contains(search_kw, case=False).any(), axis=1)
                display_df = display_df[mask]
                
            if "발생일자" in display_df.columns:
                display_df = display_df.sort_values(by="발생일자", ascending=False).reset_index(drop=True)

            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info(f"총 {len(display_df)} 건의 이력이 검색되었습니다.")
        else:
            st.info("아직 등록된 Jam 이력이 없습니다.")
