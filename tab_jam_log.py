# tab_jam_log.py
import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS

class JamLogTab:
    def __init__(self, db_jam, df_error_master):
        self.db_jam = db_jam
        # 알람 마스터 데이터를 클래스 내부에 저장합니다.
        self.df_error_master = df_error_master

    def render(self):
        st.subheader("🚨 장비별 Jam & 트러블슈팅 이력 관리")
        df_jam, _ = self.db_jam.load()

        # ==========================================
        # 1. 새로운 Jam 이력 입력부 (연동형 드롭다운 적용)
        # ==========================================
        st.markdown("### ➕ 새로운 Jam/장애 이력 등록")
        
        # 시각적인 구분을 위해 박스 형태로 감쌉니다
        st.markdown("<div style='border: 1px solid #ddd; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # 1-1. 기초 정보 (날짜 및 장비)
        c1, c2 = st.columns(2)
        with c1:
            date_val = st.date_input("발생 일자")
        with c2:
            equip_val = st.selectbox("장비명", EQUIPMENT_OPTIONS)

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # 1-2. 모듈 및 알람 연동 영역
        # 해당 장비명에 맞는 데이터만 필터링합니다 (대소문자 무시, 앞뒤 공백 제거 기준)
        if not self.df_error_master.empty and "장비명" in self.df_error_master.columns:
            filtered_by_equip = self.df_error_master[
                self.df_error_master["장비명"].astype(str).str.strip().str.upper() == equip_val.strip().upper()
            ]
        else:
            filtered_by_equip = pd.DataFrame()

        c3, c4 = st.columns(2)

        with c3:
            # 장비에 맞는 모듈 리스트 추출
            if not filtered_by_equip.empty and "모듈" in filtered_by_equip.columns:
                module_options = filtered_by_equip["모듈"].dropna().unique().tolist()
            else:
                module_options = []
            
            module_options.append("📝 직접 입력") # 리스트 맨 끝에 '직접 입력' 추가
            
            selected_module = st.selectbox("모듈(위치) 선택", module_options)
            
            # '직접 입력' 선택 시 텍스트 창 렌더링
            if selected_module == "📝 직접 입력":
                final_module = st.text_input("모듈명을 직접 입력하세요", key="manual_mod")
            else:
                final_module = selected_module

        with c4:
            # 선택한 장비 + 모듈에 맞는 알람 리스트 추출
            filtered_by_module = pd.DataFrame()
            if not filtered_by_equip.empty and final_module and final_module != "📝 직접 입력":
                filtered_by_module = filtered_by_equip[filtered_by_equip["모듈"].astype(str).str.strip() == final_module.strip()]

            if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns and "발생현상" in filtered_by_module.columns:
                # 사용자가 보기 편하게 "Err-402 (Robot Slip)" 형태로 합쳐서 보여줍니다.
                alarm_list = (filtered_by_module["알람코드"].astype(str) + " (" + filtered_by_module["발생현상"].astype(str) + ")").unique().tolist()
            else:
                alarm_list = []
                
            alarm_list.append("📝 직접 입력")

            selected_alarm = st.selectbox("알람 코드 및 현상 (타이핑하여 검색 가능)", alarm_list)

            # '직접 입력' 선택 시 코드와 현상을 따로 입력받음
            if selected_alarm == "📝 직접 입력":
                col_a, col_b = st.columns(2)
                with col_a: final_alarm_code = st.text_input("알람 코드 (예: Err-999)", key="manual_code")
                with col_b: final_issue = st.text_input("발생 현상 입력", key="manual_issue")
            else:
                # "Err-402 (Robot Slip)" 형태에서 괄호를 기준으로 코드와 현상 분리 추출
                try:
                    final_alarm_code = selected_alarm.split(" (")[0].strip()
                    final_issue = selected_alarm.split(" (")[1].replace(")", "").strip()
                except IndexError:
                    final_alarm_code = selected_alarm
                    final_issue = selected_alarm

        st.markdown("<hr style='margin: 10px 0px;'>", unsafe_allow_html=True)

        # 1-3. 조치 내역 및 상태
        action_val = st.text_input("🛠️ 조치 내역 (자세히 적어주세요)")

        c5, c6, c7 = st.columns(3)
        with c5:
            result_val = st.selectbox("조치 결과", ["✅ 완료(양호)", "👀 모니터링 중", "⚠️ 임시조치(재발가능)"])
        with c6:
            downtime_val = st.number_input("DownTime (정지 시간/분)", min_value=0)
        with c7:
            cip_val = st.selectbox("CIP(개선) 상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        # 1-4. 저장 버튼
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
                
                # 빈칸(NaN)을 빈 문자열("")로 치환하여 에러 방지 후 저장
                combined_df = pd.concat([df_jam, new_data], ignore_index=True).fillna("")
                self.db_jam.save(combined_df)
                st.success("✅ 조치 이력이 성공적으로 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 발생현상, 조치내역은 필수 입력 항목입니다. 빠진 곳이 없는지 확인해 주세요.")

        st.markdown("</div>", unsafe_allow_html=True)

        # ==========================================
        # 2. 과거 이력 검색 및 데이터 확인
        # ==========================================
        st.markdown("### 🔍 과거 트러블슈팅 이력 통합 검색")
        
        c8, c9 = st.columns([1, 3])
        with c8:
            filter_equip = st.selectbox("장비명 필터", ["전체"] + EQUIPMENT_OPTIONS, key="filter_equip")
        with c9:
            search_kw = st.text_input("검색어 입력 (알람코드, 현상, 조치내역 등 통합 검색)", placeholder="예: Err-402, 슬립, 로봇")
        
        display_df = df_jam.copy()
        
        # 검색 로직
        if not display_df.empty:
            if filter_equip != "전체":
                display_df = display_df[display_df["장비명"] == filter_equip]
                
            if search_kw:
                # 모든 열의 내용을 문자열로 바꾼 뒤, 대소문자 무시하고 검색어가 포함된 행만 필터링
                mask = display_df.apply(lambda row: row.astype(str).str.contains(search_kw, case=False).any(), axis=1)
                display_df = display_df[mask]
                
            # 최신 일자가 위로 오도록 정렬 (날짜 기준 역순)
            if "발생일자" in display_df.columns:
                display_df = display_df.sort_values(by="발생일자", ascending=False).reset_index(drop=True)

            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.info(f"총 {len(display_df)} 건의 이력이 검색되었습니다.")
        else:
            st.info("아직 등록된 Jam 이력이 없습니다.")
