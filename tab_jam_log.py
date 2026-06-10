import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 글씨 크기 축소 및 극한의 여백 압축 CSS
        # ==========================================
        st.markdown("""
            <style>
            /* 전체 여백 축소 */
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
            
            /* 입력창 라벨(제목) 글씨 크기 축소 */
            .stTextInput label p, .stSelectbox label p, .stDateInput label p, .stTimeInput label p { 
                font-size: 13px !important; 
                margin-bottom: 2px !important; 
                color: #444 !important; 
            }
            
            /* 입력창 자체 높이 및 글씨 크기 축소 */
            .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input { 
                font-size: 13px !important; 
                min-height: 32px !important; 
                height: 32px !important; 
                padding: 4px 10px !important;
            }
            
            /* 미니 아이콘 버튼 세팅 (글자 제거, 아이콘만 표출) */
            .icon-btn button { 
                padding: 0px !important; 
                height: 32px !important; 
                min-height: 32px !important; 
                font-size: 16px !important; 
                margin-top: 24px !important; /* 라벨 높이만큼 아래로 내림 */
            }
            
            /* 구분선 및 박스 세팅 */
            hr { margin: 5px 0px 10px 0px !important; padding: 0px !important; border-top: 1px solid #ccc; }
            .tight-box { border: 1.5px solid #d3d9df; padding: 15px 15px; border-radius: 8px; background-color: #f8fafc; margin-bottom: 10px; }
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
        # Jam 작성부 (요청하신 완벽한 레이아웃 배치)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # 윗줄과 아랫줄 컨테이너 생성 (알람명 선택 시 윗줄 알람코드가 바뀌도록 논리적 구조 분리)
        row1 = st.container()
        row2 = st.container()

        # ▶ 첫 번째 줄 분할: 일자 | 시간 | 장비명 | 모듈 | 알람코드 || 📝 | ✏️ | 🗑️
        r1_cols = row1.columns([1.1, 1.1, 1.2, 1.2, 1.2, 0.4, 0.4, 0.4])
        
        with r1_cols[0]: date_val = st.date_input("발생일자", value=datetime.today())
        with r1_cols[1]: time_val = st.time_input("발생시간", value="now", step=60)
        with r1_cols[2]: equip_val = st.selectbox("장비명", EQUIPMENT_OPTIONS)

        # 마스터 데이터 불러오기
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

        with r1_cols[3]:
            if not df_error_master.empty and "모듈" in df_error_master.columns:
                module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique()))
            else:
                module_options = ["(데이터 없음)"]
            selected_module = st.selectbox("모듈", module_options)

        # ▶ 두 번째 줄 분할: 알람명 (검색) | 조치내역 | CIP상태
        r2_cols = row2.columns([2.5, 4, 1.5])
        
        with r2_cols[0]:
            name_options = []
            filtered_by_module = pd.DataFrame()
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람명" in filtered_by_module.columns:
                    name_options = sorted(list(filtered_by_module["알람명"].dropna().astype(str).str.strip().unique()))
            
            if not name_options:
                name_options = ["(데이터 없음)"]
                
            selected_alarm_name = st.selectbox("알람명 (타이핑 검색)", name_options)

        # 알람명을 기반으로 알람코드 찾기 (다시 첫 번째 줄 우측에 배치)
        auto_code = ""
        if selected_alarm_name != "(데이터 없음)" and not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
            match = filtered_by_module[filtered_by_module["알람명"].astype(str).str.strip() == selected_alarm_name]
            if not match.empty:
                auto_code = match.iloc[0]["알람코드"]

        with r1_cols[4]:
            final_code = st.text_input("알람코드", value=auto_code)

        # 첫 번째 줄 우측 끝: 아이콘 버튼 배치 (툴팁 적용)
        with r1_cols[5]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝", help="저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1_cols[6]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️", help="수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1_cols[7]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_del = st.button("🗑️", help="삭제", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 두 번째 줄 나머지 항목
        with r2_cols[1]:
            action_val = st.text_input("조치내역")
        with r2_cols[2]:
            cip_val = st.selectbox("CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        st.markdown("</div>", unsafe_allow_html=True)

        # 📝 저장(작성) 버튼 로직
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
