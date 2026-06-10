import streamlit as st
import pandas as pd
from datetime import datetime
from config import EQUIPMENT_OPTIONS, DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # 글씨 크기 통일, 명암 조절, 공백 제거를 위한 완벽한 CSS
        # ==========================================
        st.markdown("""
            <style>
            /* 1. 상하단 기본 흰색 여백 제거 */
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            
            /* 2. 각 입력창의 상하 간격(공백) 축소 */
            .stTextInput, .stSelectbox, .stDateInput, .stTimeInput { margin-bottom: -15px !important; }
            
            /* 3. 라벨(제목) 명암/글씨체 수정 (완전 검은색, 굵게) */
            div[data-testid="stWidgetLabel"] p { 
                font-size: 13px !important; 
                font-weight: 800 !important; /* 글씨 굵게 */
                color: #111111 !important;   /* 완전 검은색으로 명암 대비 높임 */
                margin-bottom: 2px !important; 
            }
            
            /* 4. 드롭다운 및 입력창 내부 글씨 크기 통일 (발생일자와 동일하게 강제 축소) */
            input, div[data-baseweb="select"] * { 
                font-size: 13px !important; 
            }
            
            /* 5. 모든 창의 높이 통일 */
            input, div[data-baseweb="select"] {
                min-height: 32px !important; 
                height: 32px !important; 
                padding: 4px 10px !important;
            }
            
            /* 6. 미니 아이콘 버튼 세팅 (입력창과 라인 맞춤) */
            .icon-btn button { 
                padding: 0px !important; 
                height: 32px !important; 
                min-height: 32px !important; 
                font-size: 16px !important; 
                margin-top: 24px !important; /* 위쪽 라벨 공간만큼 밀어냄 */
            }
            
            /* 7. 전체 폼 배경 박스 (위쪽 공백 제거를 위해 마진 0 적용) */
            .tight-box { 
                border: 1px solid #d3d9df; 
                padding: 15px 15px 25px 15px; 
                border-radius: 8px; 
                background-color: #f8fafc; 
                margin-top: 5px; 
                margin-bottom: 15px; 
            }
            </style>
        """, unsafe_allow_html=True)

        # 상단 네비게이션
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
        if selected_menu != st.session_state.get('current_menu'):
            st.session_state['current_menu'] = selected_menu; st.rerun()

        df_jam, _ = self.db_jam.load()

        # ==========================================
        # Jam 작성부 (요청하신 순서 및 레이아웃)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1: 발생일자 | 발생시간 | 장비명 | 모듈 | 알람코드 | 📝 | ✏️ | 🗑️
        r1 = st.columns([1.1, 1.1, 1.2, 1.2, 1.2, 0.4, 0.4, 0.4])
        
        with r1[0]: date_val = st.date_input("발생일자", value=datetime.today())
        with r1[1]: time_val = st.time_input("발생시간", value="now", step=60)
        with r1[2]: equip_val = st.selectbox("장비명", EQUIPMENT_OPTIONS)

        # 마스터 데이터 로드
        target_sheet = f"{equip_val}_ErrorList".replace(" ", "").lower()
        df_error_master = pd.DataFrame()
        try:
            client = self.db_jam.client
            spreadsheet = client.open_by_key(self.db_jam.spreadsheet_id)
            for ws in spreadsheet.worksheets():
                if ws.title.replace(" ", "").lower() == target_sheet:
                    db_error = DataManager(self.db_jam.spreadsheet_id, ws.title)
                    df_error_master, _ = db_error.load()
                    if not df_error_master.empty:
                        df_error_master.columns = df_error_master.columns.str.strip()
                    break
        except Exception:
            pass

        with r1[3]:
            module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique())) if not df_error_master.empty and "모듈" in df_error_master.columns else ["(데이터 없음)"]
            selected_module = st.selectbox("모듈", module_options)

        with r1[4]:
            code_options = []
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                    code_options = sorted(list(filtered_by_module["알람코드"].dropna().astype(str).str.strip().unique()))
            if not code_options:
                code_options = ["(데이터 없음)"]
            
            selected_code = st.selectbox("알람코드", code_options)

        # 미니 아이콘 버튼 (글자 없이 툴팁 적용)
        with r1[5]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝", help="저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[6]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️", help="수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[7]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_del = st.button("🗑️", help="삭제", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ▶ Row 2: 알람명 (자동 완성)
        auto_alarm_name = ""
        if selected_code != "(데이터 없음)" and not df_error_master.empty:
            match = df_error_master[(df_error_master["모듈"].astype(str).str.strip() == selected_module) & (df_error_master["알람코드"].astype(str).str.strip() == selected_code)]
            if not match.empty and "알람명" in match.columns:
                auto_alarm_name = match.iloc[0]["알람명"]
                
        final_name = st.text_input("알람명", value=auto_alarm_name)

        # ▶ Row 3: 조치내역 + CIP상태
        r3 = st.columns([4, 1.5])
        with r3[0]: action_val = st.text_input("조치내역")
        with r3[1]: cip_val = st.selectbox("CIP상태", ["해당 없음", "접수 대기", "본사 검토중", "적용 완료"])

        st.markdown("</div>", unsafe_allow_html=True)

        # 📝 저장(작성) 버튼 로직
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
