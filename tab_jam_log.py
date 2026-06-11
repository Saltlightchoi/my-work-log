import streamlit as st
import pandas as pd
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # ★ Session State 초기화
        # ==========================================
        if "err_code" not in st.session_state: st.session_state.err_code = ""
        if "err_point" not in st.session_state: st.session_state.err_point = ""
        if "err_msg" not in st.session_state: st.session_state.err_msg = ""

        # ==========================================
        # ★ 무적의 자동완성 로직 (띄어쓰기, 대소문자 무시)
        # ==========================================
        def autofill(source_field):
            equip_name = st.session_state.get("equip_val", "SLH1 #1")
            
            try:
                # 지정된 컬럼 포맷을 강제하지 않고, 현재 탭(Jam List)을 있는 그대로 전부 스캔합니다.
                db_err = DataManager(self.db_jam.spreadsheet_id, equip_name)
                df_err, _ = db_err.load()
                if df_err.empty: return 
            except Exception: 
                return # 탭이 없으면 조용히 종료
            
            # 사용자가 방금 입력한 값
            search_val = str(st.session_state[source_field]).strip()
            if not search_val: return
            
            # [핵심] 엑셀 시트의 컬럼명이 "Error Code"든 "Errorcode"든 다 찾아내는 함수
            def get_real_col(target):
                target_clean = target.lower().replace(" ", "")
                for c in df_err.columns:
                    if str(c).lower().replace(" ", "") == target_clean:
                        return c
                return None

            col_code = get_real_col("errorcode")
            col_point = get_real_col("err.point")
            col_msg = get_real_col("errormasage")
            
            source_to_col = {"err_code": col_code, "err_point": col_point, "err_msg": col_msg}
            search_col = source_to_col.get(source_field)
            
            if search_col and search_col in df_err.columns:
                # 1. 100% 일치하는 값 찾기
                match = df_err[df_err[search_col].astype(str).str.strip() == search_val]
                
                # 2. 없으면 단어가 '포함된' 값 찾기
                if match.empty: 
                    match = df_err[df_err[search_col].astype(str).str.contains(search_val, case=False, na=False)]
                
                # 3. 과거 이력 중 '가장 최근(마지막)' 데이터로 채워넣기
                if not match.empty:
                    row = match.iloc[-1] 
                    
                    if source_field != "err_code" and col_code: 
                        st.session_state.err_code = str(row[col_code])
                    if source_field != "err_point" and col_point: 
                        st.session_state.err_point = str(row[col_point])
                    if source_field != "err_msg" and col_msg: 
                        st.session_state.err_msg = str(row[col_msg])

        DB_SHEET_OPTIONS = ["SLH1 #1", "SLH1 #4"]

        # ========================================================
        # 🚨 UI 레이아웃 CSS (정돈된 상태 유지)
        # ========================================================
        st.markdown("""
            <style>
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }

            div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] > div {
                height: 38px !important; min-height: 38px !important;
            }
            div[data-testid="stSelectbox"]:first-of-type div[data-baseweb="select"] span {
                font-size: 15px !important; font-weight: 800 !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stWidgetLabel"] { 
                height: 16px !important; min-height: 16px !important; margin-bottom: 4px !important; 
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stWidgetLabel"] p { 
                font-size: 12px !important; font-weight: 700 !important; line-height: 1 !important; color: #222 !important; 
            }

            div[data-testid="stVerticalBlockBorderWrapper"] input { 
                height: 32px !important; min-height: 32px !important; font-size: 13px !important; 
                padding: 0px 8px !important; box-sizing: border-box !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] > div { 
                height: 32px !important; min-height: 32px !important; padding-top: 0px !important; padding-bottom: 0px !important; 
                box-sizing: border-box !important;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] span { 
                font-size: 13px !important; 
            }

            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {
                gap: 0.1rem !important; 
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] { 
                gap: 0.5rem !important; margin-bottom: -5px !important; 
            }
            
            ul[role="listbox"] li { font-size: 13px !important; min-height: 26px !important; padding: 2px 8px !important; }

            .stButton > button { 
                height: 32px !important; min-height: 32px !important; font-size: 13px !important; padding: 0px 10px !important; 
                margin-top: 20px !important; 
            }
            
            hr { margin-top: 5px !important; margin-bottom: 5px !important; }
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
            selected_menu = st.selectbox("메뉴 이동", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
            if selected_menu != st.session_state.get('current_menu'):
                st.session_state['current_menu'] = selected_menu; st.rerun()
                
        with nav_cols[1]: btn_write = st.button("📝 저장", use_container_width=True)
        with nav_cols[2]: btn_edit = st.button("✏️ 수정", use_container_width=True)
        with nav_cols[3]: btn_del = st.button("🗑️ 삭제", use_container_width=True)

        # ==========================================
        # 입력 폼 (이벤트 트리거 완벽 연결)
        # ==========================================
        with st.container(border=True):
            r1 = st.columns([1.8, 1.2, 1.0, 1.2, 1.2, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명", DB_SHEET_OPTIONS, key="equip_val")
            with r1[1]: date_val = st.date_input("Date", value=datetime.today())
            with r1[2]: time_val = st.time_input("Err.Time", value="now", step=60)
            with r1[3]: total_unit_val = st.text_input("Totalunit")
            with r1[4]: err_code_val = st.text_input("ErrorCode", key="err_code", on_change=autofill, args=("err_code",))
            with r1[5]: err_cnt_val = st.text_input("ErrorCount", value="1")

            r2 = st.columns([1.5, 4.0, 1.5])
            with r2[0]: err_point_val = st.text_input("Err.Point", key="err_point", on_change=autofill, args=("err_point",))
            with r2[1]: err_msg_val = st.text_input("ErrorMassage", key="err_msg", on_change=autofill, args=("err_msg",))
            
            category_options = [
                "S/W Logic 불량", "H/W 불량, 파손", "H/W 소모성 교체", "H/W 셋업, 조정",
                "자재 불량", "작업자 실수", "기타", "작업실수로 인한 재발생", "원익파악불가", "장비대여불가,추후 대응"
            ]
            with r2[2]: type_val = st.selectbox("분류", category_options)

            r3 = st.columns([1, 1])
            with r3[0]: symp_val = st.text_input("현상")
            with r3[1]: cause_val = st.text_input("원인")

            r4 = st.columns([5.0, 0.6])
            with r4[0]: action_val = st.text_input("조치")
            with r4[1]: worker_val = st.text_input("조치자")

            r5 = st.columns([1, 1, 1, 3.5]) 
            with r5[0]: mtba_val = st.text_input("MTBA")
            with r5[1]: mttr_val = st.text_input("MTTR")
            with r5[2]: mtbi_val = st.text_input("MTBI")

            part_no_val, qty_val, in_date_val, out_date_val, action_loc_val, result_val = "", "", "", "", "", ""
            
            if type_val == "H/W 불량, 파손":
                st.markdown("<hr>", unsafe_allow_html=True)
                r6 = st.columns([1.5, 0.8, 1.2, 1.2, 1.5, 1.2])
                with r6[0]: part_no_val = st.text_input("도번 (Part No.)")
                with r6[1]: qty_val = st.text_input("수량")
                with r6[2]: in_date_val = st.text_input("입고일")
                with r6[3]: out_date_val = st.text_input("반입일")
                with r6[4]: action_loc_val = st.text_input("조치위치")
                with r6[5]: result_val = st.selectbox("조치결과", ["완료", "진행중", "대기"])

        # ==========================================
        # DB 연결 및 저장 로직
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

        if btn_write:
            if db_machine is None:
                st.error("🚨 구글 시트 탭이 연결되지 않아 저장할 수 없습니다. 탭 이름을 먼저 확인해 주세요.")
            elif err_code_val and err_msg_val:
                try:
                    final_err_cnt = int(err_cnt_val)
                except ValueError:
                    final_err_cnt = 1 

                new_data = pd.DataFrame([{
                    "Date": date_val.strftime("%Y-%m-%d"),
                    "Totalunit": total_unit_val,
                    "Errorcode": err_code_val,
                    "Errorcount": final_err_cnt,
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
                st.success(f"✅ '{equip_val}' 시트에 데이터가 정상적으로 저장되었습니다.")
                
                st.session_state.err_code = ""
                st.session_state.err_point = ""
                st.session_state.err_msg = ""
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
