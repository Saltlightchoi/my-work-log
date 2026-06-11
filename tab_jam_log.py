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
        if 'current_menu' not in st.session_state: st.session_state['current_menu'] = "🚨 Jam & 트러블슈팅 이력"

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
        # 🚨 [해결 1] 상단 탭 메뉴를 드롭다운(selectbox)에서 분리
        # ========================================================
        # 이제 상단 메뉴는 selectbox가 아니므로, 아래 CSS가 메뉴 글자를 줄이지 못합니다.
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        
        # 라디오 버튼을 가로형으로 배치하여 탭처럼 보이게 만듦 (크기 유지)
        st.markdown(
            """<style>
            div.row-widget.stRadio > div{flex-direction:row; align-items: center; justify-content: center; background-color: #f0f2f6; padding: 10px; border-radius: 10px;}
            div.row-widget.stRadio > div > label {font-size: 16px !important; font-weight: bold !important; margin: 0 10px;}
            </style>""", unsafe_allow_html=True
        )
        
        top_cols = st.columns([7, 3])
        with top_cols[0]:
            selected_menu = st.radio("메뉴 이동", menu_options, index=menu_options.index(st.session_state['current_menu']), label_visibility="collapsed", horizontal=True)
            if selected_menu != st.session_state['current_menu']:
                st.session_state['current_menu'] = selected_menu
                st.rerun()
                
        with top_cols[1]:
            btn_cols = st.columns(3)
            with btn_cols[0]: btn_write = st.button("📝 저장", use_container_width=True)
            with btn_cols[1]: btn_edit = st.button("✏️ 수정", use_container_width=True)
            with btn_cols[2]: btn_del = st.button("🗑️ 삭제", use_container_width=True)


        # ========================================================
        # 🚨 [해결 2] 폼 내부 전용 CSS (드롭다운 축소 + 줄 간격 파괴)
        # ========================================================
        st.markdown("""
            <style>
            /* 1. 상하 여백 조절 */
            .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
            
            /* ---------------------------------------------------- */
            /* ★ [입력 폼 내부]: 폰트 13px 통일 및 폼 컨트롤 축소 ★ */
            /* ---------------------------------------------------- */
            /* 라벨(제목) */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stWidgetLabel"] { 
                min-height: 12px !important; margin-bottom: -8px !important; 
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stWidgetLabel"] p { 
                font-size: 12px !important; font-weight: bold !important; color: #333 !important; 
            }
            
            /* 텍스트, 날짜, 숫자 입력창 높이/글자 고정 */
            div[data-testid="stVerticalBlockBorderWrapper"] input { 
                font-size: 13px !important; min-height: 28px !important; height: 28px !important; padding: 0px 8px !important;
            }
            
            /* ★ 드롭다운 박스 확실하게 축소 (상단 메뉴는 이제 라디오버튼이므로 영향 안 받음) ★ */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] * { 
                font-size: 13px !important; 
            }
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] > div { 
                min-height: 28px !important; height: 28px !important; padding-top: 0px !important; padding-bottom: 0px !important; 
            }
            ul[role="listbox"] li { font-size: 13px !important; min-height: 24px !important; padding: 2px 8px !important; }

            /* ---------------------------------------------------- */
            /* ★ [줄 간격 파괴]: 모든 여백을 음수로 당겨버림 ★ */
            /* ---------------------------------------------------- */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] { gap: 0rem !important; }
            div[data-testid="stVerticalBlockBorderWrapper"] div.element-container { margin-bottom: -15px !important; }
            
            /* 가로로 나뉜 컬럼 안쪽의 위아래 마진 제거 */
            div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="column"] > div { margin-top: 0px !important; margin-bottom: 0px !important; padding-bottom: 0px !important;}
            
            /* hr 선 얇게 */
            div[data-testid="stVerticalBlockBorderWrapper"] hr { margin-top: 5px !important; margin-bottom: 5px !important; border-top: 1px solid #ddd; }
            </style>
        """, unsafe_allow_html=True)


        # ==========================================
        # 입력 폼
        # ==========================================
        st.markdown("<br>", unsafe_allow_html=True) # 탭 메뉴와 폼 사이 간격 확보
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
            category_options = ["S/W Logic 불량", "H/W 불량, 파손", "H/W 소모성 교체", "H/W 셋업, 조정", "자재 불량", "작업자 실수", "기타", "작업실수로 인한 재발생", "원익파악불가", "장비대여불가,추후 대응"]
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
        # DB 연결 및 저장 (기존과 동일)
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
                st.error("🚨 구글 시트 연결 실패.")
            elif err_code_val and err_msg_val:
                new_data = pd.DataFrame([{
                    "Date": date_val.strftime("%Y-%m-%d"), "Totalunit": total_unit_val, "Errorcode": err_code_val,
                    "Errorcount": err_cnt_val, "Error Masage": err_msg_val, "현상": symp_val, "원인": cause_val,
                    "조치": action_val, "Err.Point": err_point_val, "분류": type_val, "조치자": worker_val,
                    "Err. Time": time_val.strftime("%H:%M"), "MTBA": mtba_val, "MTTR": mttr_val, "MTBI": mtbi_val,
                    "도번": part_no_val, "수량": qty_val, "입고일": in_date_val, "반입일": out_date_val,
                    "조치위치": action_loc_val, "조치결과": result_val
                }])
                db_machine.save(pd.concat([df_machine, new_data], ignore_index=True).fillna(""))
                st.success(f"✅ '{equip_val}' 저장 완료.")
                st.session_state.err_code = ""; st.session_state.err_point = ""; st.session_state.err_msg = ""
                st.rerun()
            else:
                st.error("🚨 ErrorCode와 ErrorMassage 필수 입력.")
                
        if btn_edit or btn_del:
            st.info("💡 아래 표를 직접 클릭해서 고치거나 지운 후 [변경사항 저장]을 누르세요.")

        st.markdown(f"#### 🔍 {equip_val} 누적 이력 조회")
        if db_machine is not None and not df_machine.empty:
            df_display = df_machine.copy()
            if "Date" in df_display.columns: df_display = df_display.sort_values(by=["Date", "Err. Time"], ascending=[False, False]).reset_index(drop=True)
            edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, num_rows="dynamic")
            if st.button(f"💾 '{equip_val}' 표 변경사항 저장", type="primary"):
                db_machine.save(edited_df.fillna(""))
                st.success("✅ 변경사항 저장됨!")
                st.rerun()
        elif db_machine is not None:
            st.info(f"'{equip_val}' 데이터 없음.")
