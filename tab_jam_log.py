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

        def autofill(source_field):
            equip_name = st.session_state.get("equip_val", "SLH1 #1")
            target_error_tab = "SLH1_Rdimm_ErrorList" if "#1" in equip_name else "SLH1_Socamm_ErrorList"
            try:
                db_err = DataManager(self.db_jam.spreadsheet_id, target_error_tab)
                df_err, _ = db_err.load()
                if not df_err.empty: df_err.columns = df_err.columns.astype(str).str.strip()
            except Exception: return 
            
            search_val = str(st.session_state[source_field]).strip()
            if not search_val or df_err.empty: return
            
            col_map = {"err_code": "알람코드", "err_point": "모듈", "err_msg": "알람명"}
            search_col = col_map.get(source_field)
            if search_col in df_err.columns:
                match = df_err[df_err[search_col].astype(str).str.strip() == search_val]
                if match.empty: match = df_err[df_err[search_col].astype(str).str.contains(search_val, case=False, na=False)]
                if not match.empty:
                    row = match.iloc[0]
                    if source_field != "err_code" and "알람코드" in df_err.columns: st.session_state.err_code = str(row["알람코드"])
                    if source_field != "err_point" and "모듈" in df_err.columns: st.session_state.err_point = str(row["모듈"])
                    if source_field != "err_msg" and "알람명" in df_err.columns: st.session_state.err_msg = str(row["알람명"])

        DB_SHEET_OPTIONS = ["SLH1 #1", "SLH1 #4"]

        # ========================================================
        # 🚨 실패를 딛고 수정한 '절대 잘리지 않는' CSS 🚨
        # ========================================================
        st.markdown("""
            <style>
            /* 1. 상단 여백 정리 */
            .block-container { padding-top: 2.5rem !important; padding-bottom: 1rem !important; }
            
            /* ---------------------------------------------------- */
            /* ★ 2. 가장 안전한 줄 간격 축소법 (마이너스 마진 삭제) ★ */
            /* ---------------------------------------------------- */
            /* 위험한 margin-bottom 음수 값을 삭제하고, 스트림릿 고유의 Gap만 0으로 만듭니다. */
            div[data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
            div[data-testid="stHorizontalBlock"] { gap: 0.2rem !important; }

            /* 라벨(제목) 밑의 불필요한 공백만 살짝 당깁니다 */
            div[data-testid="stWidgetLabel"] { 
                margin-bottom: -5px !important; 
                min-height: auto !important; 
            }
            div[data-testid="stWidgetLabel"] p { 
                font-size: 13px !important; 
                font-weight: 700 !important; 
                color: #222 !important; 
            }
            
            /* ---------------------------------------------------- */
            /* ★ 3. 모든 입력창 글자 크기 13px 강제 통일 ★ */
            /* ---------------------------------------------------- */
            div[data-testid="stTextInput"] input, 
            div[data-testid="stNumberInput"] input, 
            div[data-testid="stDateInput"] input, 
            div[data-testid="stTimeInput"] input { 
                font-size: 13px !important; 
                padding: 4px 10px !important;
            }
            
            /* ---------------------------------------------------- */
            /* ★ 4. 드롭다운 '절반 날아감' 원천 차단 ★ */
            /* ---------------------------------------------------- */
            /* 모든 하위 태그(*)에 13px을 뿌려서 멍청하게 커지는 것을 차단 */
            div[data-baseweb="select"] * { 
                font-size: 13px !important; 
            }
            /* 글자를 자르던 멍청한 height 고정을 없애고, min-height와 패딩으로만 얇게 만듦 */
            div[data-baseweb="select"] > div { 
                min-height: 34px !important; 
                padding-top: 2px !important; 
                padding-bottom: 2px !important; 
            }
            
            /* 드롭다운 리스트(팝업) 폰트도 통일 */
            ul[role="listbox"] li { 
                font-size: 13px !important; 
                padding-top: 4px !important; 
                padding-bottom: 4px !important; 
                min-height: 25px !important; 
            }

            /* ---------------------------------------------------- */
            /* 5. 우측 버튼 정렬 */
            /* ---------------------------------------------------- */
            .stButton > button { 
                min-height: 34px !important; 
                font-size: 13px !important; 
                padding: 4px 10px !important; 
                margin-top: 24px !important; /* 버튼 위치 보정 */
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
            # 전체 폰트를 13px로 맞추었기 때문에 이 메뉴도 13px로 출력됩니다.
            selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
            if selected_menu != st.session_state.get('current_menu'):
                st.session_state['current_menu'] = selected_menu; st.rerun()
                
        with nav_cols[1]: btn_write = st.button("📝 저장", use_container_width=True)
        with nav_cols[2]: btn_edit = st.button("✏️ 수정", use_container_width=True)
        with nav_cols[3]: btn_del = st.button("🗑️ 삭제", use_container_width=True)

        # ==========================================
        # 입력 폼
        # ==========================================
        with st.container(border=True):
            r1 = st.columns([1.8, 1.2, 1.0, 1.2, 1.2, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명", DB_SHEET_OPTIONS, key="equip_val")
            with r1[1]: date_val = st.date_input("Date", value=datetime.today())
            with r1[2]: time_val = st.time_input("Err.Time", value="now", step=60)
            with r1[3]: total_unit_val = st.text_input("Totalunit")
            with r1[4]: err_code_val = st.text_input("ErrorCode", key="err_code", on_change=autofill, args=("err_code",))
            with r1[5]: err_cnt_val = st.number_input("ErrorCount", min_value=1, value=1, step=1)

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
