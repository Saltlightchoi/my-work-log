import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        st.subheader("🚨 장비별 Jam & 트러블슈팅 이력 관리")
        df_jam, _ = self.db_jam.load()

        # ==========================================
        # 1. 새로운 Jam 이력 입력부 (장비별 시트 자동 연동)
        # ==========================================
        st.markdown("### ➕ 새로운 Jam/장애 이력 등록")
        st.markdown("<div style='border: 1px solid #ddd; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # 1-1. 기초 정보 (날짜 및 장비)
        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("발생 일자")
        with c2:
            equip_val = st.selectbox("장비명", EQUIPMENT_OPTIONS)

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # ★ 핵심 로직: 선택된 장비의 ErrorList 시트를 실시간으로 찾아옴
        # (예: SLH1 선택 -> "SLH1_ErrorList" 시트 데이터 불러오기)
        # ---------------------------------------------------------
        sheet_name_for_error = f"{equip_val}_ErrorList"
        
        try:
            # db_jam의 스프레드시트 ID를 재활용하여 해당 장비 시트 연결
            db_error = DataManager(self.db_jam.spreadsheet_id, sheet_name_for_error)
            df_error_master, _ = db_error.load()
        except Exception:
            # 아직 구글 시트에 해당 장비의 ErrorList 탭을 만들지 않았다면 빈 상태로 둡니다.
            df_error_master = pd.DataFrame()

        c3, c4 = st.columns(2)

        with c3:
            # 해당 장비 시트에서 '모듈' 리스트만 쏙 빼옵니다.
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
            # 선택한 모듈에 맞는 알람 리스트만 추출
            filtered_by_module = pd.DataFrame()
            if not df_error_master.empty and final_module and final_module != "📝 직접 입력":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == final_module.strip()]

            # ★ 수정된 부분: '발생현상' 대신 '알람명'을 찾도록 변경했습니다.
            if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns and "알람명" in filtered_by_module.columns:
                # "Err-402 (Robot Slip)" 형태로 묶어서 보여줍니다.
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
                # 괄호를 기준으로 코드와 알람명 분리 추출
                try:
                    final_alarm_code = selected_alarm.split(" (")[0].strip()
                    final_issue = selected_alarm.split(" (")[1].replace(")", "").strip()
                except IndexError:
                    final_alarm_code = selected_alarm
                    final_issue = selected_alarm

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # 1-3. 조치 내역 및 상태 수기 입력
        action_val = st.text_input("🛠️ 조치 내역 (자세히 적어주세요)")

        c5, c6, c7 = st.columns(3)
        with c5:
            result_val = st.selectbox("조치 결과", ["✅ 완료(양호)", "👀 모니터링 중", "⚠️ 임시조치(재발가능)"])
        with c6:
            downtime_val = st.number_input("DownTime (정지 시간/분)", min_value=0)
        with c7:
            cip_val = st.selectbox("CIP(개선) 상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 1-4. DB 저장 버튼
        if st.button("💾 Jam 이력 저장", type="primary", use_container_width=True):
            if final_module and final_alarm_code and final_issue and action_val:
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), 
                    "장비명": equip_val,
                    "모듈(위치)": final_module, 
                    "알람코드": final_alarm_code, 
                    # app.py에 선언된 DB 헤더가 '발생현상'이므로 그곳에 '알람명' 데이터를 넣어줍니다.
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
        
        # 검색 로직
        if not display_df.empty:
            if filter_equip != "전체":
                display_df = display_df[display_df["장비명"] == filter_equip]
                
            if search_kw:
                mask = display_df.apply(lambda row: row.astype(str).str.contains(search_kw, case=False).any(), axis=1)
                display_df = display_df[mask]
                
            # 최신 일자가 위로 오도록 정렬
            if "발생일자" in display_df.columns:
                display_df = display_df.sort_values(by="발생일자", ascending=False).reset_index(drop=True)

            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info(f"총 {len(display_df)} 건의 이력이 검색되었습니다.")
        else:
            st.info("아직 등록된 Jam 이력이 없습니다.")
