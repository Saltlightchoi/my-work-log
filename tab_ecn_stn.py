import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime
import openpyxl
from config import EQUIPMENT_OPTIONS

class ECNSTNTab:
    def __init__(self, db_ecn):
        self.db_ecn = db_ecn

    def render(self):
        st.markdown("<div class='main-title'>🛠️ ECN & STN (장비 파트 및 수정사항 관리)</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        ecn_base_path = r"\\192.168.0.100\500 생산\550 국내CS\ECN&STN"
        bad_base_path = r"\\192.168.0.100\500 생산\550 국내CS\ECT&STN"

        col1, col2, col3, col_search = st.columns([1.5, 1.5, 2.5, 4.5])
        with col1: equipment = st.selectbox("장비 선택", EQUIPMENT_OPTIONS, key="ecn_equip")
        with col2: unit = st.selectbox("호기 선택", ["전체"] + [f"{i}호기" for i in range(1, 16)], key="ecn_unit")
        
        with col3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            show_help = st.checkbox("💡 도움말 및 수정방법 보기")
                
        with col_search:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            search_keyword = st.text_input("🔍 내용/ECN No. 검색", placeholder="예: ECN-005, 실린더 교체 등", label_visibility="collapsed")

        if show_help:
            st.info("**이용 안내:** 구글 시트 **`ECN_STN`** 탭을 기반으로 목록을 출력합니다.\n\n"
                    "표의 **'조치현황'**, **'특이사항'**, **'첨부(파일명 입력)'** 칸을 더블 클릭하여 내용을 직접 수정할 수 있습니다. 수정한 뒤엔 하단의 **저장 버튼**을 눌러주세요.\n\n"
                    "**📁 첨부파일/원본 열기 팁:**\n"
                    "웹 브라우저 표에서 복사할 때 따옴표가 3개(`\"\"\"`)로 증식하는 버그를 완벽히 피하기 위해 화면 하단에 **[1초 복사기]**를 만들었습니다.\n"
                    "1. 표의 **'첨부(파일명 입력)'** 칸에는 **확장자 없이 파일명만** 적으셔도 자동으로 PDF로 연결됩니다.\n"
                    "2. 열고 싶은 항목의 파일 이름을 복사(`Ctrl+C`)합니다.\n"
                    "3. 표 밑에 있는 **'1초 복사기'** 칸에 붙여넣기 하시면 완벽한 주소가 생성됩니다!\n"
                    "4. 키보드에서 **`[윈도우키 + R]`**을 눌러 붙여넣고 엔터를 치면 파일이 바로 열립니다.")

        try:
            df_raw, _ = self.db_ecn.load()
            
            if df_raw.empty or len(df_raw.columns) == 0:
                df_raw = pd.DataFrame(columns=['날짜', '발행부서', '발행자', '장비호기', 'ECN No', 'AS-IS', 'TO-BE', '특이사항', '조치현황', '첨부'])

            orig_cols = df_raw.columns.tolist()
            new_cols = []
            col_idx_map = {} 
            seen_cols = set()
            
            for i, c in enumerate(orig_cols):
                c_clean = str(c).replace(" ", "").upper()
                base_col = str(c).strip()
                
                if '날짜' in c_clean or '일자' in c_clean: base_col = '날짜'
                elif '발행부서' in c_clean: base_col = '발행부서'
                elif '발행자' in c_clean or '작성자' in c_clean: base_col = '발행자'
                elif '장비호기' in c_clean or '호기' in c_clean: base_col = '장비호기'
                elif 'ECN' in c_clean or '문서번호' in c_clean: base_col = 'ECN No'
                elif 'AS-IS' in c_clean or 'ASIS' in c_clean or '내용' in c_clean: base_col = 'AS-IS'
                elif 'TO-BE' in c_clean or 'TOBE' in c_clean or '변경' in c_clean: base_col = 'TO-BE'
                elif '특이사항' in c_clean or '비고' in c_clean: 
                    base_col = '특이사항'
                    col_idx_map['특이사항'] = base_col
                elif '조치' in c_clean or '진행' in c_clean: 
                    base_col = '조치현황'
                    col_idx_map['조치현황'] = base_col
                elif '첨부' in c_clean: 
                    base_col = '첨부'
                    col_idx_map['첨부'] = base_col

                if base_col in seen_cols:
                    base_col = f"{base_col}_{i}"
                seen_cols.add(base_col)
                new_cols.append(base_col)
            
            df_raw.columns = new_cols
            
            df_raw['Original_Index'] = df_raw.index
            df = df_raw.copy()
            
            if '장비호기' in df.columns:
                df = df[df['장비호기'].astype(str).str.contains(equipment, case=False, na=False)].copy()

            if '장비호기' in df.columns:
                if unit == "전체":
                    filtered_df = df.copy()
                else:
                    target_match = re.search(r'(\d+)호기', unit)
                    target_num = int(target_match.group(1)) if target_match else -1
                    
                    def check_match(val):
                        if pd.isna(val): return False
                        val_str = str(val).lower()
                        if unit.lower() in val_str: return True
                        ranges = re.findall(r'(\d+)\s*[~-]\s*(\d+)', val_str)
                        for s_str, e_str in ranges:
                            s, e = int(s_str), int(e_str)
                            if s > e: s, e = e, s
                            if s <= target_num <= e: return True
                        return False

                    mask = df['장비호기'].apply(check_match)
                    filtered_df = df[mask].copy()
            elif '발행부서' in df.columns: 
                filtered_df = df.copy()
            else:
                st.error("⚠️ 시트 컬럼을 인식할 수 없습니다. 구글 시트 1행의 양식을 확인해주세요.")
                return

            if search_keyword:
                filtered_df = filtered_df[filtered_df.apply(lambda r: search_keyword.lower() in str(r).lower(), axis=1)]
                
            expected_cols = ['Original_Index', '날짜', '발행부서', '발행자', 'ECN No', 'AS-IS', 'TO-BE', '특이사항', '조치현황', '첨부']
            display_cols = [c for c in expected_cols if c in filtered_df.columns]
            filtered_df = filtered_df[display_cols].copy()
            
            if '날짜' in filtered_df.columns:
                import datetime as dt
                def parse_date_robust(d):
                    if isinstance(d, dt.time): return pd.NaT
                    if isinstance(d, (dt.datetime, dt.date)): return pd.to_datetime(d)
                    try:
                        if pd.isna(d): return pd.NaT
                    except: pass
                    d_str = str(d).strip()
                    if d_str in ['', 'nan', 'NaN', 'None', 'nat', 'NaT', '0.0']: return pd.NaT
                    if d_str.replace('.', '', 1).isdigit():
                        try:
                            val = float(d_str)
                            if 30000 < val < 80000: return pd.to_datetime(val, unit='D', origin='1899-12-30')
                        except: pass
                    try: 
                        d_str_clean = d_str.replace('.', '-').replace('/', '-')
                        return pd.to_datetime(d_str_clean, errors='coerce')
                    except: return pd.NaT
                        
                filtered_df['TempDate'] = filtered_df['날짜'].apply(parse_date_robust)
                filtered_df = filtered_df.dropna(subset=['TempDate'])
                
                # ★ 에러 수정: 데이터가 있을 때만 datetime 변환을 실행하도록 방어
                if not filtered_df.empty:
                    filtered_df['TempDate'] = pd.to_datetime(filtered_df['TempDate'])
                    filtered_df = filtered_df.sort_values(by='TempDate', ascending=False)
                    filtered_df['날짜'] = filtered_df['TempDate'].dt.strftime('%Y-%m-%d')
                
                filtered_df = filtered_df.drop(columns=['TempDate'], errors='ignore')
                
            filtered_df = filtered_df.astype(str).replace(['nan', 'NaN', 'None', 'nat', 'NaT', '0.0'], '')
            filtered_df.reset_index(drop=True, inplace=True)
            
            if '첨부' in filtered_df.columns:
                def clean_attachment(val):
                    if pd.isna(val): return ""
                    val_str = str(val).strip().replace('"', '') 
                    if val_str.startswith(bad_base_path):
                        val_str = val_str[len(bad_base_path):].lstrip("\\")
                    if val_str.startswith(ecn_base_path):
                        return val_str[len(ecn_base_path):].lstrip("\\")
                    return val_str
                
                filtered_df['첨부(파일명)'] = filtered_df['첨부'].apply(clean_attachment)
            
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            if not filtered_df.empty:
                total_cnt = len(filtered_df)
                done_cnt = 0
                prog_cnt = 0
                if '조치현황' in filtered_df.columns:
                    done_cnt = len(filtered_df[filtered_df['조치현황'].astype(str).str.contains('완료', na=False)])
                    prog_cnt = len(filtered_df[filtered_df['조치현황'].astype(str).str.contains('진행중|진행 중', na=False)])
                pend_cnt = total_cnt - done_cnt - prog_cnt
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("📌 검색된 총 건수", f"{total_cnt} 건")
                m2.metric("✅ 조치 완료", f"{done_cnt} 건")
                m3.metric("⏳ 진행중", f"{prog_cnt} 건")
                m4.metric("🚨 미조치 (대기)", f"{pend_cnt} 건")
            
            st.markdown("<br>", unsafe_allow_html=True)

            if not filtered_df.empty:
                disabled_cols = [c for c in filtered_df.columns if c not in ['특이사항', '조치현황', '첨부(파일명)']]
                
                def highlight_status(val):
                    val_str = str(val).strip()
                    if '완료' in val_str: return 'background-color: #d4edda; color: #155724; font-weight: bold;'
                    if '진행' in val_str: return 'background-color: #fff3cd; color: #856404; font-weight: bold;'
                    if '대기' in val_str or val_str == '': return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
                    return ''

                if '조치현황' in filtered_df.columns:
                    styled_df = filtered_df.style.map(highlight_status, subset=['조치현황'])
                else:
                    styled_df = filtered_df

                col_cfg = {"Original_Index": None}
                if "첨부" in filtered_df.columns: col_cfg["첨부"] = None
                if "AS-IS" in filtered_df.columns: col_cfg["AS-IS"] = st.column_config.TextColumn("AS-IS", width="large")
                if "TO-BE" in filtered_df.columns: col_cfg["TO-BE"] = st.column_config.TextColumn("TO-BE", width="large")
                if "특이사항" in filtered_df.columns: col_cfg["특이사항"] = st.column_config.TextColumn("특이사항", width="medium")
                if "조치현황" in filtered_df.columns: col_cfg["조치현황"] = st.column_config.SelectboxColumn("조치현황", options=["대기", "진행중", "완료"], width="small")
                
                if "첨부(파일명)" in filtered_df.columns: 
                    col_cfg["첨부(파일명)"] = st.column_config.TextColumn("첨부(파일명 입력)", width="medium")

                edited_df = st.data_editor(
                    styled_df, 
                    use_container_width=True, 
                    hide_index=True,
                    disabled=disabled_cols,
                    column_config=col_cfg,
                    key=f"ecn_editor_safe_{equipment}_{unit}_{search_keyword}"
                )
                
                st.markdown("---")
                st.markdown("#### 🚀 원본 파일 바로 열기 (1초 복사기)")
                st.info("웹 표에서 복사하면 따옴표가 늘어나는 버그가 있어 만든 전용 복사기입니다. 위 표에서 **파일명만 복사**해서 아래에 붙여넣어 주세요.")
                
                run_target = st.text_input("여기에 파일명을 붙여넣으세요:", placeholder="예: SLH1-PP-260306-01(5건)", label_visibility="collapsed")
                if run_target:
                    clean_target = run_target.strip().replace('"', '')
                    if clean_target.startswith(bad_base_path):
                        clean_target = clean_target[len(bad_base_path):].lstrip("\\")
                    if clean_target.startswith(ecn_base_path):
                        clean_target = clean_target[len(ecn_base_path):].lstrip("\\")
                    
                    if clean_target and not clean_target.lower().endswith('.pdf') and not clean_target.startswith("http"):
                        clean_target += ".pdf"
                        
                    final_run_path = f"{ecn_base_path}\\{clean_target}"
                    
                    st.success("✨ 변환 완료! 아래 회색 박스 우측 상단의 **[복사 아이콘(📋)]**을 클릭하고 `[Win + R]` 창에 붙여넣기 하세요.")
                    st.code(final_run_path, language="text")
                
                action_col1, action_col2, action_col3 = st.columns([2, 2, 6])
                
                with action_col1:
                    save_btn = st.button("💾 변경사항 구글 시트에 저장하기", type="primary", use_container_width=True)
                
                with action_col2:
                    output_excel = io.BytesIO()
                    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                        cols_to_drop = ['Original_Index', '첨부(파일명)']
                        filtered_df.drop(columns=cols_to_drop, errors='ignore').to_excel(writer, index=False, sheet_name='ECN_Data')
                    st.download_button(
                        label="📥 현재 리스트 엑셀 다운로드",
                        data=output_excel.getvalue(),
                        file_name=f"ECN_{equipment}_{unit}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                with st.expander("➕ 새 ECN 항목 구글 시트에 바로 등록하기"):
                    with st.form("add_new_ecn_form", clear_on_submit=True):
                        st.write("아래 내용을 작성하여 등록하면 구글 시트 맨 아래에 자동으로 추가됩니다.")
                        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                        n_date = f_col1.date_input("날짜")
                        n_dept = f_col2.text_input("발행부서")
                        n_author = f_col3.text_input("발행자")
                        n_unit = f_col4.text_input("장비호기", value=f"{equipment} {unit if unit != '전체' else ''}")
                        
                        n_ecn = st.text_input("ECN No (예: ECN-001)")
                        f_col5, f_col6 = st.columns(2)
                        n_asis = f_col5.text_area("AS-IS (수정 전)")
                        n_tobe = f_col6.text_area("TO-BE (수정 후)")
                        
                        f_col7, f_col8, f_col9 = st.columns([2, 1, 2])
                        n_note = f_col7.text_input("특이사항")
                        n_status = f_col8.selectbox("조치현황", ["대기", "진행중", "완료"])
                        n_attach = f_col9.text_input("첨부 (파일명만 입력)", placeholder="예: SLH1-PP-260306-01")
                        
                        if st.form_submit_button("새 항목 등록하기"):
                            new_row_dict = {}
                            for c in df_raw.columns:
                                if c == 'Original_Index': continue
                                c_clean = str(c).replace(" ", "").upper()
                                if '날짜' in c_clean or '일자' in c_clean: new_row_dict[c] = str(n_date)
                                elif '발행부서' in c_clean: new_row_dict[c] = n_dept
                                elif '발행자' in c_clean or '작성자' in c_clean: new_row_dict[c] = n_author
                                elif '장비호기' in c_clean or '호기' in c_clean: new_row_dict[c] = n_unit
                                elif 'ECN' in c_clean or '문서번호' in c_clean: new_row_dict[c] = n_ecn
                                elif 'AS-IS' in c_clean or 'ASIS' in c_clean or '내용' in c_clean: new_row_dict[c] = n_asis
                                elif 'TO-BE' in c_clean or 'TOBE' in c_clean or '변경' in c_clean: new_row_dict[c] = n_tobe
                                elif '특이사항' in c_clean or '비고' in c_clean: new_row_dict[c] = n_note
                                elif '조치' in c_clean or '진행' in c_clean: new_row_dict[c] = n_status
                                elif '첨부' in c_clean: 
                                    n_attach_clean = n_attach.strip().replace('"', '')
                                    if n_attach_clean and not n_attach_clean.lower().endswith('.pdf') and not n_attach_clean.startswith("http") and not n_attach_clean.startswith("\\\\"):
                                        n_attach_clean += ".pdf"
                                        
                                    if n_attach_clean.startswith(bad_base_path):
                                        n_attach_clean = n_attach_clean[len(bad_base_path):].lstrip("\\")
                                    if n_attach_clean and not n_attach_clean.startswith("\\\\") and not n_attach_clean.startswith("http"):
                                        new_row_dict[c] = f"{ecn_base_path}\\{n_attach_clean}"
                                    else:
                                        new_row_dict[c] = n_attach_clean
                                else:
                                    new_row_dict[c] = ""
                            
                            df_new_row = pd.DataFrame([new_row_dict])
                            df_final = pd.concat([df_raw.drop(columns=['Original_Index'], errors='ignore'), df_new_row], ignore_index=True)
                            self.db_ecn.save(df_final)
                            
                            st.success("✅ 새 ECN 항목이 구글 시트에 추가되었습니다! 화면을 새로고침 합니다.")
                            st.rerun()

                if save_btn:
                    try:
                        changes_made = False
                        for _, row in edited_df.iterrows():
                            orig_idx = int(row['Original_Index'])
                            
                            if '특이사항' in col_idx_map:
                                col_name = col_idx_map['특이사항']
                                if str(df_raw.at[orig_idx, col_name]) != str(row.get('특이사항', '')):
                                    df_raw.at[orig_idx, col_name] = row.get('특이사항', '')
                                    changes_made = True
                                    
                            if '조치현황' in col_idx_map:
                                col_name = col_idx_map['조치현황']
                                if str(df_raw.at[orig_idx, col_name]) != str(row.get('조치현황', '')):
                                    df_raw.at[orig_idx, col_name] = row.get('조치현황', '')
                                    changes_made = True
                                    
                            if '첨부' in col_idx_map:
                                col_name = col_idx_map['첨부']
                                fname = str(row.get('첨부(파일명)', '')).strip().replace('"', '')
                                if fname.startswith(bad_base_path):
                                    fname = fname[len(bad_base_path):].lstrip("\\")
                                    
                                if fname and not fname.lower().endswith('.pdf') and not fname.startswith("http") and not fname.startswith("\\\\"):
                                    fname += ".pdf"
                                    
                                if fname and not fname.startswith("\\\\") and not fname.startswith("http"):
                                    full_path = f"{ecn_base_path}\\{fname}"
                                else:
                                    full_path = fname
                                    
                                if str(df_raw.at[orig_idx, col_name]) != str(full_path):
                                    df_raw.at[orig_idx, col_name] = full_path
                                    changes_made = True
                                    
                        if changes_made:
                            self.db_ecn.save(df_raw.drop(columns=['Original_Index'], errors='ignore'))
                            st.success("✅ 구글 시트에 성공적으로 저장되었습니다! 화면을 새로고침 합니다.")
                            st.rerun()
                        else:
                            st.warning("저장할 변경사항이 없습니다.")
                    except Exception as save_err:
                        st.error(f"구글 시트 저장 중 오류가 발생했습니다: {save_err}")

            else:
                st.warning(f"선택하신 조건에 해당하는 데이터가 없습니다. (또는 시트가 비어있습니다)")
                
        except Exception as e:
            st.error(f"⚠️ 데이터를 읽는 중 오류가 발생했습니다: {e}")
