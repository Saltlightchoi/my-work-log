import streamlit as st
import pandas as pd
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # ★ 호기별 탭 세팅 (필요시 수정)
        # ==========================================
        DB_SHEET_OPTIONS = [
            "아산 우익반도체 SLH1 #1",
            "아산 우익반도체 SLH1 #4"
        ]

        # ==========================================
        # UI 여백 제거 및 CSS 세팅
        # ==========================================
        st.markdown("""
            <style>
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            .tight-box { 
                border: 1px solid #d3d9df; padding: 15px; border-radius: 8px; 
                background-color: #f8fafc; margin-top: -5px !important; margin-bottom: 15px !important; 
            }
            .tight-box div[data-testid="stWidgetLabel"] {
                display: block !important; visibility: visible !important; margin-bottom: 4px !important;
            }
            .tight-box div[data-testid="stWidgetLabel"] p { 
                font-size: 13px !important; font-weight: 800 !important; color: #000000 !important; 
            }
            .tight-box input, .tight-box div[data-baseweb="select"] * { font-size: 13px !important; }
            .tight-box input, .tight-box div[data-baseweb="select"] { 
                min-height: 34px !important; height: 34px !important; padding: 4px 10px !important;
            }
            .icon-btn button { 
                padding: 0px !important; height: 34px !important; min-height: 34px !important; 
                font-size: 16px !important; margin-top: 26px !important; 
            }
            .tight-box div[data-testid="stSelectbox"], .tight-box div[data-testid="stTextInput"], 
            .tight-box div[data-testid="stDateInput"], .tight-box div[data-testid="stTimeInput"], 
            .tight-box div[data-testid="stNumberInput"] { margin-bottom: 0px !important; }
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

        # ==========================================
        # 21개 항목 입력 폼 (분류별로 줄을 나누어 꽉 차게 배치)
        # ==========================================
        st.markdown("<div class='tight-box'>", unsafe_allow_html=True)

        # ▶ Row 1 (기본 정보): Date | Err. Time | 조치자 | 장비선택 | 저장버튼
        r1 = st.columns([1, 1, 1, 1.5, 0.4, 0.4, 0.4])
        with r1[0]: date_val = st.date_input("Date (날짜)", value=datetime.today())
        with r1[1]: time_val = st.time_input("Err. Time", value="now", step=60)
        with r1[2]: worker_val = st.text_input("조치자")
        with r1[3]: equip_val = st.selectbox("장비명 (저장될 시트)", DB_SHEET_OPTIONS)
        
        # 버튼들
        with r1[4]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_write = st.button("📝", help="저장", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[5]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_edit = st.button("✏️", help="수정", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with r1[6]: 
            st.markdown("<div class='icon-btn'>", unsafe_allow_html=True)
            btn_del = st.button("🗑️", help="삭제", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ▶ Row 2 (에러 정보): Err.Point | Errorcode | Error Masage | Errorcount
        r2 = st.columns([1.5, 1, 3, 1])
        with r2[0]: err_point_val = st.text_input("Err.Point (발생위치)")
        with r2[1]: err_code_val = st.text_input("Errorcode")
        with r2[2]: err_msg_val = st.text_input("Error Masage")
        with r2[3]: err_cnt_val = st.number_input("Errorcount", min_value=1, value=1, step=1)

        # ▶ Row 3 (원인 및 조치): 분류 | 현상 | 원인 | 조치 | 조치결과 | 조치위치
        r3 = st.columns([1, 2, 2, 2, 1, 1])
        with r3[0]: type_val = st.selectbox("분류", ["H/W", "S/W", "자재불량", "작업자실수", "기타"])
        with r3[1]: symp_val = st.text_input("현상")
        with r3[2]: cause_val = st.text_input("원인")
        with r3[3]: action_val = st.text_input("조치")
        with r3[4]: result_val = st.selectbox("조치결과", ["완료", "진행중", "대기"])
        with r3[5]: action_loc_val = st.text_input("조치위치")

        # ▶ Row 4 (지표 및 자재): Totalunit | MTBA | MTTR | MTBI | 도번 | 수량 | 입고일 | 반입일
        r4 = st.columns([1, 1, 1, 1, 1.5, 0.8, 1, 1])
        with r4[0]: total_unit_val = st.text_input("Totalunit")
        with r4[1]: mtba_val = st.text_input("MTBA")
        with r4[2]: mttr_val = st.text_input("MTTR")
        with r4[3]: mtbi_val = st.text_input("MTBI")
        with r4[4]: part_no_val = st.text_input("도번 (Part No.)")
        with r4[5]: qty_val = st.text_input("수량")
        with r4[6]: in_date_val = st.text_input("입고일")
        with r4[7]: out_date_val = st.text_input("반입일")

        st.markdown("</div>", unsafe_allow_html=True)

        # DB 연결 및 데이터 21개 항목 매핑
        target_db_tab = equip_val
        # 대표님이 적어주신 정확한 21개 컬럼 리스트
        exact_columns = [
            "Date", "Totalunit", "Errorcode", "Errorcount", "Error Masage", 
            "현상", "원인", "조치", "Err.Point", "분류", "조치자", "Err. Time", 
            "MTBA", "MTTR", "MTBI", "도번", "수량", "입고일", "반입일", "조치위치", "조치결과"
        ]
        
        db_machine = DataManager(self.db_jam.spreadsheet_id, target_db_tab, exact_columns)
        try:
            df_machine, _ = db_machine.load()
        except Exception:
            df_machine = pd.DataFrame(columns=exact_columns)

        # 📝 저장 로직
        if btn_write:
            if err_code_val and err_msg_val: # 필수항목 조건 (수정가능)
                new_data = pd.DataFrame([{
                    "Date": date_val.strftime("%Y-%m-%d"),
                    "Totalunit": total_unit_val,
                    "Errorcode": err_code_val,
                    "Errorcount": err_cnt_val,
                    "Error Masage": err_msg_val,
                    "현상": symp_val,
                    "원인": cause_val,
                    "조치": action_val,
                    "Err.Point": err_point_val,
                    "분류": type_val,
                    "조치자": worker_val,
                    "Err. Time": time_val.strftime("%H:%M"),
                    "MTBA": mtba_val,
                    "MTTR": mttr_val,
                    "MTBI": mtbi_val,
                    "도번": part_no_val,
                    "수량": qty_val,
                    "입고일": in_date_val,
                    "반입일": out_date_val,
                    "조치위치": action_loc_val,
                    "조치결과": result_val
                }])
                db_machine.save(pd.concat([df_machine, new_data], ignore_index=True).fillna(""))
                st.success(f"✅ '{target_db_tab}' 시트에 데이터가 정상적으로 저장되었습니다.")
                st.rerun()
            else:
                st.error("🚨 Errorcode와 Error Masage는 필수 입력 항목입니다.")

        # 통합 조회 표
        st.markdown(f"#### 🔍 {equip_val} 누적 이력 조회")
        if not df_machine.empty:
            df_display = df_machine.copy()
            if "Date" in df_display.columns:
                df_display = df_display.sort_values(by=["Date", "Err. Time"], ascending=[False, False]).reset_index(drop=True)
            
            edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, num_rows="dynamic")

            if st.button(f"💾 '{target_db_tab}' 표 변경사항 저장", type="secondary"):
                db_machine.save(edited_df.fillna(""))
                st.success("✅ 변경사항이 저장되었습니다!")
                st.rerun()
        else:
            st.info(f"'{target_db_tab}' 시트에 등록된 데이터가 없습니다. (구글 시트의 A1~U1 첫 줄에 21개 열 이름을 똑같이 적어주세요)")
