import streamlit as st
import pandas as pd
import io
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # 상단에 보이지 않는 안전 여백을 주어 천장 짤림을 원천 방지
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

        # ========================================================
        # 🚨 UI 레이아웃 CSS (★ 멍청한 구역 제한자 완전히 삭제! 진짜 원본 복구 ★)
        # ========================================================
        st.markdown("""
            <style>
            /* 1. 드롭다운 껍데기 높이 32px 강제 고정 */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { 
                height: 32px !important; min-height: 32px !important; 
                padding-top: 0px !important; padding-bottom: 0px !important; 
                box-sizing: border-box !important;
            }
            
            /* 2. 드롭다운 안의 '모든' 글자 크기 13px 강제 축소 (span, div 전부 타겟팅) */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] div { 
                font-size: 13px !important; 
                line-height: normal !important;
            }

            /* 3. 사이드바의 탭 메뉴는 무조건 크게 유지 */
            [data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                height: 38px !important; min-height: 38px !important;
            }
            [data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
            [data-testid="stSidebar"] div[data-testid="stSelectbox"] div[data-baseweb="select"] div {
                font-size: 15px !important; font-weight: bold !important;
            }

            /* 4. 일반 텍스트, 날짜, 숫자 입력창 높이 32px 완벽 고정 */
            input { 
                height: 32px !important; min-height: 32px !important; font-size: 13px !important; 
                padding: 0px 8px !important; box-sizing: border-box !important;
            }

            /* 5. 라벨(제목) 높이와 아래 여백 압축 */
            div[data-testid="stWidgetLabel"] { 
                height: 16px !important; min-height: 16px !important; margin-bottom: 2px !important; 
            }
            div[data-testid="stWidgetLabel"] p { 
                font-size: 12px !important; font-weight: 700 !important; line-height: 1 !important; color: #222 !important; 
            }

            /* 6. 위아래, 좌우 간격(Gap) 조절 */
            div[data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
            /* 숨통을 틔워주는 줄 사이 간격 2px */
            div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; margin-bottom: 2px !important; }

            /* 7. 드롭다운 클릭 시 리스트 크기 13px 압축 */
            ul[role="listbox"] li { 
                font-size: 13px !important; min-height: 26px !important; padding: 2px 8px !important; 
            }

            /* 8. ★ 버튼 테두리 짤림 방지 ★ */
            .stButton > button { 
                height: 32px !important; min-height: 32px !important; font-size: 13px !important; 
                padding: 0px 10px !important; margin-top: 15px !important; 
            }
            </style>
        """, unsafe_allow_html=True)

        # ==========================================
        # ★ 제목과 액션 버튼 한 줄에 안정적으로 배치
        # ==========================================
        header_cols = st.columns([5.5, 1, 1, 1, 1.5]) 
        
        with header_cols[0]:
            st.markdown("<div style='font-size: 22px; font-weight: 700; padding-top: 15px;'>🚨 Jam & 트러블슈팅 이력</div>", unsafe_allow_html=True)
            
        with header_cols[1]: 
            btn_write = st.button("📝 저장", use_container_width=True)
        with header_cols[2]: 
            btn_edit = st.button("✏️ 수정", use_container_width=True)
        with header_cols[3]: 
            btn_del = st.button("🗑️ 삭제", use_container_width=True)
        with header_cols[4]:
            search_btn_text = "❌ 검색 종료" if st.session_state.get('search_mode', False) else "🔍 상세 검색"
            if st.button(search_btn_text, use_container_width=True):
                st.session_state.search_mode = not st.session_state.get('search_mode', False)
                st.session_state.clear_form = True 
                st.rerun()

        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        # ==========================================
        # Session State 초기화
        # ==========================================
        TEXT_KEYS = [
            "err_code", "err_point", "err_msg", "total_unit", "err_cnt", 
            "symp", "cause", "action", "worker", "mtba", "mttr", "mtbi",
            "part_no", "qty", "in_date", "out_date", "action_loc", "date_search"
        ]
        for k in TEXT_KEYS:
            if k not in st.session_state: st.session_state[k] = ""
            
        if "clear_form" not in st.session_state: st.session_state.clear_form = False
        if "save_success_msg" not in st.session_state: st.session_state.save_success_msg = ""
        if "search_mode" not in st.session_state: st.session_state.search_mode = False

        if st.session_state.clear_form:
            for k in TEXT_KEYS: st.session_state[k] = ""
            st.session_state.err_cnt = "1" 
            st.session_state.clear_form = False
            
        if st.session_state.save_success_msg:
            st.success(st.session_state.save_success_msg)
            st.session_state.save_success_msg = ""

        # ==========================================
        # 자동완성 로직 (★ 6월 14일 원본 로직 유지 + 정밀 매칭 필터 적용)
        # ==========================================
        def autofill(source_field):
            if st.session_state.search_mode: return 
            
            equip_name = st.session_state.get("equip_val", "SLH1 #1")
            
            # 1호기: R-dimm 탭 / 4~7호기: SoCAMM 탭 참조
            if equip_name == "SLH1 #1": 
                target_error_tab = "SLH1_R-Dimm&LPCAMM ErrorList"
            elif equip_name in ["SLH1 #4", "SLH1 #5", "SLH1 #6", "SLH1 #7"]: 
                target_error_tab = "SLH1_SoCAMM ErrorList"
            else: 
                target_error_tab = "SLH1_R-Dimm&LPCAMM ErrorList"
                
            try:
                # ✅ 검증된 원본 방식(.load)으로 정상 파싱
                db_err = DataManager(self.db_jam.spreadsheet_id, target_error_tab)
                df_err, _ = db_err.load()
                if df_err.empty: return 
            except Exception as e:
                # 연결 실패 시 침묵하지 않고 우측 하단에 에러 알림 표출
                st.toast(f"⚠️ ErrorList 로드 실패: {e}")
                return 
            
            search_val = str(st.session_state[source_field]).strip()
            if not search_val: return

            # ✅ 핵심 보완: 데이터프레임 내 숫자의 '.0' 소수점 변환 잔재 및 공백 완전 제거
            df_err = df_err.fillna("")
            for col in df_err.columns:
                df_err[col] = df_err[col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
            
            def get_real_col(*possible_names):
                for c in df_err.columns:
                    c_clean = str(c).lower().replace(" ", "")
                    for p in possible_names:
                        if c_clean == p.lower().replace(" ", ""): return c
                return None

            col_code = get_real_col("errorcode", "알람코드", "code")
            col_point = get_real_col("err.point", "모듈", "point", "errpoint")
            col_msg = get_real_col("errormasage", "알람명", "errormessage", "message", "error message")
            
            source_to_col = {"err_code": col_code, "err_point": col_point, "err_msg": col_msg}
            search_col = source_to_col.get(source_field)
            
            if search_col and search_col in df_err.columns:
                # 1차 정확한 매칭 -> 실패 시 2차 부분 매칭 시도
                match = df_err[df_err[search_col].str.lower() == search_val.lower()]
                if match.empty: 
                    match = df_err[df_err[search_col].str.contains(search_val, case=False, na=False)]
                
                if not match.empty:
                    row = match.iloc[0] 
                    if source_field != "err_code" and col_code: st.session_state.err_code = str(row[col_code])
                    if source_field != "err_point" and col_point: st.session_state.err_point = str(row[col_point])
                    if source_field != "err_msg" and col_msg: st.session_state.err_msg = str(row[col_msg])
        # ==========================================
        # 입력 및 검색 폼
        # ==========================================
        with st.container(border=True):
            if st.session_state.search_mode:
                st.info("🔍 **[검색 모드 활성화]** 빈칸에 찾고 싶은 내용을 입력하고 엔터를 누르시면, 아래 표가 실시간으로 걸러집니다.")

            r1 = st.columns([1.8, 1.2, 1.0, 1.2, 1.2, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명", DB_SHEET_OPTIONS, key="equip_val")
            with r1[1]: 
                if st.session_state.search_mode:
                    date_val_search = st.text_input("Date (예: 2024-05)", key="date_search")
                else:
                    date_val = st.date_input("Date", value=datetime.today())
            with r1[2]: time_val = st.time_input("Err.Time", value="now", step=60)
            with r1[3]: total_unit_val = st.text_input("Totalunit", key="total_unit")
            with r1[4]: err_code_val = st.text_input("ErrorCode", key="err_code", on_change=autofill, args=("err_code",))
            with r1[5]: err_cnt_val = st.text_input("ErrorCount", key="err_cnt")

            r2 = st.columns([1.5, 4.0, 1.5])
            with r2[0]: err_point_val = st.text_input("Err.Point", key="err_point", on_change=autofill, args=("err_point",))
            with r2[1]: err_msg_val = st.text_input("ErrorMassage", key="err_msg", on_change=autofill, args=("err_msg",))
            
            category_options = [
                "S/W Logic 불량", "H/W 불량, 파손", "H/W 소모성 교체", "H/W 셋업, 조정",
                "자재 불량", "작업자 실수", "기타", "작업실수로 인한 재발생", "원인파악불가", "장비대기, 추후 대응"
            ]
            if st.session_state.search_mode: category_options.insert(0, "전체") 
            with r2[2]: type_val = st.selectbox("분류", category_options, key="type_val")

            r3 = st.columns([1, 1])
            with r3[0]: symp_val = st.text_input("현상", key="symp")
            with r3[1]: cause_val = st.text_input("원인", key="cause")

            r4 = st.columns([5.0, 0.6])
            with r4[0]: action_val = st.text_input("조치", key="action")
            with r4[1]: worker_val = st.text_input("조치자", key="worker")

            r5 = st.columns([1, 1, 1, 3.5]) 
            with r5[0]: mtba_val = st.text_input("MTBA", key="mtba")
            with r5[1]: mttr_val = st.text_input("MTTR", key="mttr")
            with r5[2]: mtbi_val = st.text_input("MTBI", key="mtbi")

            part_no_val, qty_val, in_date_val, out_date_val, action_loc_val, result_val = "", "", "", "", "", ""
            
            if type_val == "H/W 불량, 파손":
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 5px;'>", unsafe_allow_html=True)
                r6 = st.columns([1.5, 0.8, 1.2, 1.2, 1.5, 1.2])
                with r6[0]: part_no_val = st.text_input("도번 (Part No.)", key="part_no")
                with r6[1]: qty_val = st.text_input("수량", key="qty")
                with r6[2]: in_date_val = st.text_input("입고일", key="in_date")
                with r6[3]: out_date_val = st.text_input("반입일", key="out_date")
                with r6[4]: action_loc_val = st.text_input("조치위치", key="action_loc")
                with r6[5]: result_val = st.selectbox("조치결과", ["완료", "진행중", "대기"], key="result")

        # ==========================================
        # DB 연결 및 데이터 로드 
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
            st.error(f"🚨 구글 시트 연결 실패: '{equip_val}' 탭 연결 중 오류가 발생했습니다. 구글 시트에 '{equip_val}' 탭이 존재하는지 확인해주세요! (상세에러: {e})")

        # 저장 로직
        if btn_write:
            if st.session_state.search_mode:
                st.warning("🚨 현재 '검색 모드'가 켜져 있습니다. 데이터를 저장하시려면 우측의 [❌ 검색 종료] 버튼을 눌러주세요.")
            elif db_machine is None:
                st.error("🚨 구글 시트 탭이 연결되지 않아 저장할 수 없습니다.")
            elif err_code_val and err_msg_val:
                try: final_err_cnt = int(err_cnt_val)
                except ValueError: final_err_cnt = 1 

                new_data = pd.DataFrame([{
                    "Date": date_val.strftime("%Y-%m-%d"), "Totalunit": total_unit_val, "Errorcode": err_code_val,
                    "Errorcount": final_err_cnt, "Error Masage": err_msg_val, "현상": symp_val, "원인": cause_val,
                    "조치": action_val, "Err.Point": err_point_val, "분류": type_val, "조치자": worker_val,
                    "Err. Time": time_val.strftime("%H:%M"), "MTBA": mtba_val, "MTTR": mttr_val, "MTBI": mtbi_val,
                    "도번": part_no_val, "수량": qty_val, "입고일": in_date_val, "반입일": out_date_val,
                    "조치위치": action_loc_val, "조치결과": result_val
                }])
                db_machine.save(pd.concat([df_machine, new_data], ignore_index=True).fillna(""))
                st.session_state.save_success_msg = f"✅ 정상 저장되었습니다."
                st.session_state.clear_form = True 
                st.rerun()
            else:
                st.error("🚨 ErrorCode와 ErrorMassage는 필수 입력 항목입니다.")

        # ==========================================
        # 통합 조회 표 및 엑셀 다운로드 
        # ==========================================
        if db_machine is not None and not df_machine.empty:
            df_display = df_machine.copy()
            
            if st.session_state.search_mode:
                if st.session_state.date_search: df_display = df_display[df_display["Date"].astype(str).str.contains(st.session_state.date_search, case=False, na=False)]
                if st.session_state.err_code: df_display = df_display[df_display["Errorcode"].astype(str).str.contains(st.session_state.err_code, case=False, na=False)]
                if st.session_state.err_point: df_display = df_display[df_display["Err.Point"].astype(str).str.contains(st.session_state.err_point, case=False, na=False)]
                if st.session_state.err_msg: df_display = df_display[df_display["Error Masage"].astype(str).str.contains(st.session_state.err_msg, case=False, na=False)]
                if type_val != "전체": df_display = df_display[df_display["분류"] == type_val]
                if st.session_state.symp: df_display = df_display[df_display["현상"].astype(str).str.contains(st.session_state.symp, case=False, na=False)]
                if st.session_state.cause: df_display = df_display[df_display["원인"].astype(str).str.contains(st.session_state.cause, case=False, na=False)]
                if st.session_state.worker: df_display = df_display[df_display["조치자"].astype(str).str.contains(st.session_state.worker, case=False, na=False)]

            if "Date" in df_display.columns:
                df_display = df_display.sort_values(by=["Date", "Err. Time"], ascending=[False, False]).reset_index(drop=True)
            
            view_cols = st.columns([7.0, 1.5, 1.5])
            with view_cols[0]:
                st.markdown(f"#### 🔍 {equip_val} 누적 이력 조회 ({len(df_display)}건)")
            with view_cols[1]:
                buffer = io.BytesIO()
                try:
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_display.to_excel(writer, index=False, sheet_name='데이터')
                    download_data = buffer.getvalue()
                    file_name = f"{equip_val}_데이터_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                except Exception:
                    download_data = df_display.to_csv(index=False).encode('utf-8-sig') 
                    file_name = f"{equip_val}_데이터_{datetime.now().strftime('%Y%m%d')}.csv"
                    mime_type = "text/csv"

                st.download_button(
                    label="📥 엑셀 다운로드", data=download_data, file_name=file_name, mime=mime_type,
                    use_container_width=True, key="jam_log_download_btn" 
                )
            with view_cols[2]:
                st.empty() 

            edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, num_rows="dynamic")

            if st.button(f"💾 '{equip_val}' 표 변경사항 저장", type="primary"):
                if st.session_state.search_mode:
                    st.warning("⚠️ 검색 모드 중에는 표 수정을 권장하지 않습니다. ❌검색 종료 버튼을 눌러 전체 표 상태에서 수정해주세요.")
                else:
                    db_machine.save(edited_df.fillna(""))
                    st.success("✅ 변경사항이 저장되었습니다!")
                    st.rerun()
        elif db_machine is not None:
            st.info(f"'{equip_val}' 시트에 등록된 데이터가 없습니다.")
