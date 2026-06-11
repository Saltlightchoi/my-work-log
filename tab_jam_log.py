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
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            div[data-testid="stWidgetLabel"] p { font-size: 14px !important; font-weight: 600 !important; color: #222 !important; }
            div[data-testid="stTextInput"] input, 
            div[data-testid="stDateInput"] input, 
            div[data-testid="stTimeInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span { font-size: 14px !important; }
            </style>
        """, unsafe_allow_html=True)

        # ==========================================
        # 상단 네비게이션 & 우측 액션 버튼
        # ==========================================
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        
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
        # 입력 폼 (대표님 요청 순서 및 동적 UI 적용)
        # ==========================================
        with st.container(border=True):
            # ▶ 1줄: 장비명, Date, Err.Time, Totalunit, ErrorCode, ErrorCount
            r1 = st.columns([1.8, 1.2, 1.0, 1.2, 1.2, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명", DB_SHEET_OPTIONS)
            with r1[1]: date_val = st.date_input("Date", value=datetime.today())
            with r1[2]: time_val = st.time_input("Err.Time", value="now", step=60)
            with r1[3]: total_unit_val = st.text_input("Totalunit")
            with r1[4]: err_code_val = st.text_input("ErrorCode")
            with r1[5]: err_cnt_val = st.number_input("ErrorCount", min_value=1, value=1, step=1)

            # ▶ 2줄: Err.Point, ErrorMassage, 분류
            r2 = st.columns([1.5, 4.0, 1.5])
            with r2[0]: err_point_val = st.text_input("Err.Point")
            with r2[1]: err_msg_val = st.text_input("ErrorMassage")
            with r2[2]: type_val = st.selectbox("분류", ["장비대여불가,추후대응", "원인파악불가","H/W 불량 파손", "S/W Bug", "자재불량", "작업자실수","작업실수로 인한 재발생", "기타"])

            # ▶ 3줄: 현상, 원인 (절반씩 넓게)
            r3 = st.columns([1, 1])
            with r3[0]: symp_val = st.text_input("현상")
            with r3[1]: cause_val = st.text_input("원인")

            # ▶ 5줄: 조치, 조치자 (조치자는 3글자 크기에 맞춰 극도로 축소)
            r4 = st.columns([5.0, 0.6])
            with r4[0]: action_val = st.text_input("조치")
            with r4[1]: worker_val = st.text_input("조치자")

            # ▶ 6줄: MTBA, MTTR, MTBI (우측에 빈 공간(여백)을 두어 억지로 늘어나지 않게 방어)
            r5 = st.columns([1, 1, 1, 3.5]) 
            with r5[0]: mtba_val = st.text_input("MTBA")
            with r5[1]: mttr_val = st.text_input("MTTR")
            with r5[2]: mtbi_val = st.text_input("MTBI")

            # ==========================================
            # ★ 7줄: 분류가 "H/W 불량 파손"일 때만 나타나는 숨겨진 폼 ★
            # ==========================================
            # 1. H/W가 아닐 때 저장될 기본값(빈칸) 세팅
            part_no_val, qty_val, in_date_val, out_date_val, action_loc_val, result_val = "", "", "", "", "", ""
            
            # 2. H/W를 선택한 경우에만 화면에 표출
            if type_val == "H/W 불량 파손":
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True) # 구분선 추가
                r6 = st.columns([1.5, 0.8, 1.2, 1.2, 1.5, 1.2])
                with r6[0]: part_no_val = st.text_input("도번 (Part No.)")
                with r6[1]: qty_val = st.text_input("수량")
                with r6[2]: in_date_val = st.text_input("입고일")
                with r6[3]: out_date_val = st.text_input("반입일")
                with r6[4]: action_loc_val = st.text_input("조치위치")
                with r6[5]: result_val = st.selectbox("조치결과", ["완료", "진행중", "대기"])

        # ==========================================
        # DB 연결 및 안전 예외 처리
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
        # 버튼 동작 로직
        # ==========================================
        if btn_write:
            if db_machine is None:
                st.error("🚨 구글 시트 탭이 연결되지 않아 저장할 수 없습니다. 탭 이름을 먼저 확인해 주세요.")
            elif err_code_val and err_msg_val:
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
                    "도번": part_no_val, # H/W가 아닐 땐 자동으로 빈칸("") 저장됨
                    "수량": qty_val,
                    "입고일": in_date_val,
                    "반입일": out_date_val,
                    "조치위치": action_loc_val,
                    "조치결과": result_val
                }])
                db_machine.save(pd.concat([df_machine, new_data], ignore_index=True).fillna(""))
                st.success(f"✅ '{equip_val}' 시트에 데이터가 정상적으로 저장되었습니다.")
                st.rerun()
            else:
                st.error("🚨 ErrorCode와 ErrorMassage는 필수 입력 항목입니다.")
                
        if btn_edit or btn_del:
            st.info("💡 데이터 수정/삭제는 아래 표(누적 이력)를 직접 클릭해서 고치거나 지운 후 표 하단의 [변경사항 저장] 버튼을 누르시면 됩니다.")

        # ==========================================
        # 통합 조회 표
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
