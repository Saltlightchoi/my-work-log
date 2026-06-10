import streamlit as st
import pandas as pd
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # ★ 장비명 세팅
        # ==========================================
        DB_SHEET_OPTIONS = [
            "SLH1 #1",
            "SLH1 #4"
        ]

        # ==========================================
        # 심플하고 안전한 CSS (글자 크기 완벽 통일)
        # ==========================================
        st.markdown("""
            <style>
            /* 상하 여백 축소 */
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            
            /* 라벨(제목) 글씨체 14px, 진하게 고정 */
            div[data-testid="stWidgetLabel"] p { 
                font-size: 13px !important; 
                font-weight: 600 !important; 
                color: #222 !important; 
            }
            
            /* ★ 입력창 및 드롭다운 내부 글씨 크기 14px 완벽 통일 ★ */
            div[data-testid="stTextInput"] input, 
            div[data-testid="stDateInput"] input, 
            div[data-testid="stTimeInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span { 
                font-size: 12px !important; 
            }
            </style>
        """, unsafe_allow_html=True)

        # ==========================================
        # 상단 네비게이션 & 우측 액션 버튼 배치
        # ==========================================
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        
        # 탭 메뉴(넓게) + 버튼 3개(좁게) 한 줄 배치
        nav_cols = st.columns([6, 1, 1, 1])
        with nav_cols[0]:
            selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
            if selected_menu != st.session_state.get('current_menu'):
                st.session_state['current_menu'] = selected_menu; st.rerun()
                
        with nav_cols[1]: btn_write = st.button("📝 저장", use_container_width=True)
        with nav_cols[2]: btn_edit = st.button("✏️ 수정", use_container_width=True)
        with nav_cols[3]: btn_del = st.button("🗑️ 삭제", use_container_width=True)

        st.markdown("---")

        # ==========================================
        # 21개 항목 입력 폼 (비율에 맞춘 칼배치)
        # ==========================================
        with st.container(border=True):
            # ▶ Row 1 (장비명 맨 앞 / 날짜, 시간, 조치자 타이트하게 압축)
            r1 = st.columns([0.5, 0.5, 0.4, 0.4, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명 (저장될 탭 선택)", DB_SHEET_OPTIONS)
            with r1[1]: date_val = st.date_input("Date (날짜)", value=datetime.today())
            with r1[2]: time_val = st.time_input("Err. Time", value="now", step=60)
            with r1[3]: worker_val = st.text_input("조치자")
            with r1[4]: total_unit_val = st.text_input("Totalunit")

            # ▶ Row 2 (Err.Point, Errorcode 축소 / 메시지는 아주 넓게)
            r2 = st.columns([1.0, 0.8, 0.5, 4.5])
            with r2[0]: err_point_val = st.text_input("Err.Point (발생위치)")
            with r2[1]: err_code_val = st.text_input("Errorcode")
            with r2[2]: err_cnt_val = st.number_input("Errorcount", min_value=1, value=1, step=1)
            with r2[3]: err_msg_val = st.text_input("Error Masage")

            # ▶ Row 3 (원인 및 조치내역)
            r3 = st.columns([0.7, 2, 2, 3])
            with r3[0]: type_val = st.selectbox("분류", ["H/W", "S/W", "자재불량", "작업자실수", "기타"])
            with r3[1]: symp_val = st.text_input("현상")
            with r3[2]: cause_val = st.text_input("원인")
            with r3[3]: action_val = st.text_input("조치")

            # ▶ Row 4 (조치 결과 및 지표)
            r4 = st.columns([0.8, 0.4, 0.4, 0.4, 0.4])
            with r4[0]: action_loc_val = st.text_input("조치위치")
            with r4[1]: result_val = st.selectbox("조치결과", ["완료", "진행중", "대기"])
            with r4[2]: mtba_val = st.text_input("MTBA")
            with r4[3]: mttr_val = st.text_input("MTTR")
            with r4[4]: mtbi_val = st.text_input("MTBI")

            # ▶ Row 5 (자재 정보)
            r5 = st.columns([0.7, 0.3, 0.4, 0.4])
            with r5[0]: part_no_val = st.text_input("도번 (Part No.)")
            with r5[1]: qty_val = st.text_input("수량")
            with r5[2]: in_date_val = st.text_input("입고일")
            with r5[3]: out_date_val = st.text_input("반입일")

        # ==========================================
        # DB 연결 및 데이터 21개 항목 매핑
        # ==========================================
        exact_columns = [
            "Date", "Totalunit", "Errorcode", "Errorcount", "Error Masage", 
            "현상", "원인", "조치", "Err.Point", "분류", "조치자", "Err. Time", 
            "MTBA", "MTTR", "MTBI", "도번", "수량", "입고일", "반입일", "조치위치", "조치결과"
        ]
        
        db_machine = None
        df_machine = pd.DataFrame(columns=exact_columns)

        try:
            db_machine = DataManager(self.db_jam.spreadsheet_id, equip_val, exact_columns)
            df_machine, _ = db_machine.load()
        except Exception as e:
            st.error(f"🚨 구글 시트 연결 실패: 새로 만드신 Jam 파일에 '{equip_val}' 이라는 이름의 탭(시트)이 없습니다.")

        # ==========================================
        # 통합 조회 표 표출 부분
        # ==========================================
        st.markdown(f"#### 🔍 {equip_val} 누적 이력 조회")
        
        if db_machine is not None and not df_machine.empty:
            df_display = df_machine.copy()
            if "Date" in df_display.columns:
                df_display = df_display.sort_values(by=["Date", "Err. Time"], ascending=[False, False]).reset_index(drop=True)
            
            edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, num_rows="dynamic")

            if st.button(f"💾 '{equip_val}' 표 변경사항 저장", type="primary"):
                db_machine.save(edited_df.fillna(""))
                st.success("✅ 변경사항이 저장되었습니다!")
                st.rerun()
        elif db_machine is not None:
            st.info(f"'{equip_val}' 시트에 등록된 데이터가 없습니다.")
