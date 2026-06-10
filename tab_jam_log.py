import streamlit as st
import pandas as pd
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam # 기본 시트 연결 ID 확보용

    def render(self):
        # ==========================================
        # ★ 장비 목록 및 에러 리스트 탭 설정 (Conversion 대응)
        # ==========================================
        DB_SHEET_OPTIONS = [
            "아산 우익반도체 SLH1 #1",
            "아산 우익반도체 SLH1 #4"
            # 추후 호기가 늘어나면 여기에 이름만 추가하시면 됩니다.
        ]
        
        ERROR_SHEET_MAPPING = {
            "Rdimm & Lpcamm": "SLH1_Rdimm_ErrorList",
            "Socamm": "SLH1_Socamm_ErrorList"
        }

        # ==========================================
        # UI 디자인 (공백 제거 및 글씨 14px 강제 고정)
        # ==========================================
        st.markdown("""
            <style>
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
            
            .tight-box { 
                border: 1px solid #d3d9df; 
                padding: 15px; 
                border-radius: 8px; 
                background-color: #f8fafc; 
                margin-top: -5px !important; 
                margin-bottom: 15px !important; 
            }
            
            .tight-box div[data-testid="stWidgetLabel"] {
                display: block !important;
                visibility: visible !important;
                margin-bottom: 4px !important;
            }
            .tight-box div[data-testid="stWidgetLabel"] p { 
                font-size: 13px !important; 
                font-weight: 800 !important; 
                color: #000000 !important; 
            }
            
            .tight-box input, 
            .tight-box div[data-baseweb="select"] * { 
                font-size: 14px !important; 
            }
            
            .tight-box input, 
            .tight-box div[data-baseweb="select"] { 
                min-height: 36px !important; 
                height: 36px !important; 
                padding: 4px 10px !important;
            }
            
            ul[role="listbox"] li, ul[data-baseweb="menu"] li {
                font-size: 14px !important;
                min-height: 36px !important;
                height: auto !important;
                white-space: normal !important;
            }
            
            .icon-btn button { 
                padding: 0px !important; 
                height: 36px !important; 
                min-height: 36px !important; 
                font-size: 16px !important; 
                margin-top: 27px !important; 
            }
            
            .tight-box div[data-testid="stSelectbox"], 
            .tight-box div[data-testid="stTextInput"], 
            .tight-box div[data-testid="stDateInput"], 
            .tight-box div[data-testid="stTimeInput"] { 
                margin-bottom: 0px !important; 
            }
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

        # ==========================================
        # Jam 작성부 (Conversion 대응 스마트 1열 배치)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1: 발생일자 | 발생시간 | 장비명(호기) | 품종(에러기준) | 모듈 | 알람코드 | 📝 | ✏️ | 🗑️
        r1 = st.columns([0.9, 0.9, 1.25, 1.1, 1.1, 1.1, 0.35, 0.35, 0.35])
        
        with r1[0]: date_val = st.date_input("발생일자", value=datetime.today())
        with r1[1]: time_val = st.time_input("발생시간", value="now", step=60)
        
        with r1[2]: 
            equip_val = st.selectbox("장비명(저장 DB)", DB_SHEET_OPTIONS)

        with r1[3]:
            # 선택된 호기에 따라 기본 품종을 자동으로 세팅 (Conversion 발생 시 수동 변경 가능)
            default_type_idx = 0 if "#1" in equip_val else 1
            error_type_val = st.selectbox("품종(에러 리스트)", list(ERROR_SHEET_MAPPING.keys()), index=default_type_idx)

        # 타겟 DB 탭과 Error 탭 확정
        target_db_tab = equip_val
        target_error_tab = ERROR_SHEET_MAPPING[error_type_val]

        # 1. 저장될 메인 DB 연결
        db_machine = DataManager(self.db_jam.spreadsheet_id, target_db_tab)
        try:
            df_machine, _ = db_machine.load()
        except Exception:
            df_machine = pd.DataFrame()

        # 2. 에러 마스터 시트 연결 (Conversion으로 바뀐 품종에 맞춰 로드됨)
        df_error_master = pd.DataFrame()
        try:
            db_error = DataManager(self.db_jam.spreadsheet_id, target_error_tab)
            df_error_master, _ = db_error.load()
            if not df_error_master.empty:
                df_error_master.columns = df_error_master.columns.str.strip()
        except Exception:
            pass

        with r1[4]:
            module_options = sorted(list(df_error_master["모듈"].dropna().astype(str).str.strip().unique())) if not df_error_master.empty and "모듈" in df_error_master.columns else ["(데이터 없음)"]
            selected_module = st.selectbox("모듈", module_options)

        with r1[5]:
            code_options = []
            if not df_error_master.empty and selected_module != "(데이터 없음)":
                filtered_by_module = df_error_master[df_error_master["모듈"].astype(str).str.strip() == selected_module]
                if not filtered_by_module.empty and "알람코드" in filtered_by_module.columns:
                    code_options = sorted(list(filtered_by_module["알람코드"].dropna().astype(str).str.strip().unique()))
            if not code_options:
                code_options = ["(데이터 없음)"]
            
            selected_code = st.selectbox("알람코드", code_options)

        # 우측 끝 미니 아이콘 버튼
        with r1[6]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝", help="저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[7]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️", help="수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[8]: 
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

        if df_error_master.empty:
            st.warning(f"🚨 구글 시트에서 선택하신 에러 기준 탭('{target_error_tab}')을 찾을 수 없거나 데이터가 비어있습니다.")

        # 📝 저장(작성) 버튼 로직
        if btn_write:
            if selected_module != "(데이터 없음)" and selected_code != "(데이터 없음)" and action_val:
                # DB에 명확히 기록하기 위해 장비명 옆에 (품종)을 붙여서 저장합니다.
                saved_equip_name = f"{equip_val} ({error_type_val})"
                
                new_data = pd.DataFrame([{
                    "발생일자": date_val.strftime("%Y-%m-%d"), "발생시간": time_val.strftime("%H:%M"),
                    "장비명": saved_equip_name, "모듈": selected_module, "알람코드": selected_code, "알람명": final_name,
                    "조치내역": action_val, "완료시간": "", "DownTime": "", "CIP상태": cip_val, 
                    "업데이트일": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                db_machine.save(pd.concat([df_machine, new_data], ignore_index=True).fillna(""))
                st.success(f"✅ '{target_db_tab}' 탭에 정상적으로 등록되었습니다!")
                st.rerun()
            else:
                st.error("🚨 모듈, 알람코드, 조치내역은 필수입니다. (데이터를 확인해 주세요.)")
        
        if btn_edit or btn_del:
            st.info("💡 수정/삭제는 하단 데이터 표 안의 항목을 클릭하여 수정하거나, 행 좌측을 선택해 키보드(Delete)로 지운 뒤 [표 변경사항 저장]을 누르시면 됩니다.")

        # ==========================================
        # 통합 이력 조회 (해당 호기 데이터 표출)
        # ==========================================
        st.markdown(f"#### 🔍 {equip_val} 누적 이력")
        
        if not df_machine.empty:
            df_display = df_machine.copy()
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

            if st.button(f"💾 '{target_db_tab}' 표 변경사항 저장 (DownTime 자동계산)", type="secondary"):
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
                
                db_machine.save(edited_df.fillna(""))
                st.success("✅ 변경사항 및 DownTime이 저장되었습니다!")
                st.rerun()
        else:
            st.info(f"'{target_db_tab}' 탭에 등록된 데이터가 없습니다. (혹은 구글시트 첫 줄 제목이 맞지 않습니다)")
