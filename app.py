import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# --- 1. UI 설정 및 스타일 ---
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")

st.markdown("""
    <style>
        .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] {
            padding: 2px 5px !important;
            font-size: 12px !important;
            min-height: 28px !important;
            height: 28px !important;
            white-space: nowrap !important;
        }
        .main-title { font-size: 1.5rem !important; font-weight: bold; margin: 0 !important; padding-bottom: 10px !important; }
        div.stDownloadButton > button { padding: 4px 10px !important; font-size: 12px !important; width: 100% !important; }
        .info-box { background-color: #1e212b; padding: 12px; border-radius: 4px; border-left: 3px solid #4CAF50; margin-bottom: 15px; font-size: 13px; }
        
        /* Expander (대항목) 타이틀 폰트 조절 */
        .streamlit-expanderHeader { font-weight: bold !important; font-size: 1.1rem !important; color: #4CAF50 !important; }
    </style>
    """, unsafe_allow_html=True)

BASE_PATH_RAW = r"\\192.168.0.100\500 생산\550 국내CS\공유사진\\"

# --- 2. GitHub 연결 설정 ---
try:
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(st.secrets["REPO_NAME"])
    LOG_FILE_PATH = st.secrets["FILE_PATH"] # 업무일지
    FLOW_FILE_PATH = "cs_flow_data.csv"     # 신규 CS Flow 파일
except Exception as e:
    st.error(f"⚠️ 연결 설정 오류: {e}")
    st.stop()

# --- 3. 데이터 로직 ---

# 업무일지 데이터 로드
def get_log_data():
    try:
        file_content = repo.get_contents(LOG_FILE_PATH)
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        df = df.loc[:, ~df.columns.duplicated()]
        for col in ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"]:
            if col not in df.columns: df[col] = ""
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date.astype(str)
        return df.sort_values(by='날짜', ascending=False).reset_index(drop=True), file_content.sha
    except:
        return pd.DataFrame(columns=["날짜", "장비", "작성자", "업무내용", "비고", "첨부"]), None

def save_log_data(df, sha, message):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    if sha: repo.update_file(LOG_FILE_PATH, message, csv_buffer.getvalue(), sha)
    else: repo.create_file(LOG_FILE_PATH, "Init", csv_buffer.getvalue())

# 장비 Flow 데이터 로드
def get_flow_data():
    try:
        file_content = repo.get_contents(FLOW_FILE_PATH)
        df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
        return df, file_content.sha
    except:
        cols = ["프로젝트명", "대항목", "순서", "작업내용", "상태", "비고", "첨부", "업데이트일"]
        return pd.DataFrame(columns=cols), None

def save_flow_data(df, sha, message):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    if sha: repo.update_file(FLOW_FILE_PATH, message, csv_buffer.getvalue(), sha)
    else: repo.create_file(FLOW_FILE_PATH, "Init", csv_buffer.getvalue())

EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# 제공해주신 엑셀 기반 CS 작업 리스트 템플릿
CS_TEMPLATE = [
    {"대항목": "공통", "순서": 1, "작업내용": "i/o Check\n- OUP PUT으로 동작 후 IN PUT LED 확인\n- Cylinder 정상 동작 및 MANUAL 확인\n- 미비된 부분 I/O LIST, PC 저장 후 수정 요청", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 2, "작업내용": "공압 Leak check", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 3, "작업내용": "Cylinder Speed 조정 및 PART 위치 조정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 4, "작업내용": "전면부 후면부 1차 Levelling (Auto Leveler 사용)", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Stacker", "순서": 5, "작업내용": "L/D 1,2, UL/D 1,2, emt, Reject Inverter 값 설정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 6, "작업내용": "Motor parameter setting 및 다회전 클리어 (S/W팀 요청)", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Hand", "순서": 7, "작업내용": "Loader unloader X,Y축 직진도 (±0.5mm) SETTING 및 측정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Hand", "순서": 8, "작업내용": "L/D, UL/D Pitch, 높이(±0.15mm) SETTING 및 측정 (Double nut 조정)", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Stacker", "순서": 9, "작업내용": "L/D, UL/D, Empty, Reject Base 평탄도(±0.2mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Transfer", "순서": 10, "작업내용": "L/D, UL/D X,Y,Z축 직진도 평탄도(±0.3mm) SETTING 및 측정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "TEST", "순서": 11, "작업내용": "Front, Rear Press 평탄도(±0.25mm) SETTING 및 측정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "TEST", "순서": 12, "작업내용": "Front, Rear Press load cell(0.2, 0.29bar) SETTING 및 측정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "TEST", "순서": 13, "작업내용": "Front, Rear T-Tray Rail 평탄도(±0.2mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Set plate", "순서": 14, "작업내용": "L/D, UL/D X축 직진도 및 평탄도(±0.2mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Set plate", "순서": 15, "작업내용": "DOWN Hard Stopper 높이 SETTING (24mm) 및 측정", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Middle", "순서": 16, "작업내용": "L/D, UL/D Gripper UP Cylinder Rod (37mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Middle", "순서": 17, "작업내용": "L/D, UL/D Rail UP/DWON 높이,평탄,직진도 SETTING (T-TRAY 사용)", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Input", "순서": 18, "작업내용": "Bottom Feeder UP Cylinder Rod(16.5mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
    {"대항목": "Output", "순서": 19, "작업내용": "Bottom Feeder UP Cylinder Rod(16.5mm) SETTING", "상태": "대기", "비고": "", "첨부": ""},
]

# 배경색 하이라이트 함수 (Pandas Styler 용)
def highlight_status(row):
    status = row['상태']
    if status == '완료':
        bg_color = '#d4edda' # 연녹색
        text_color = '#000000'
    elif status == '작업중':
        bg_color = '#fff3cd' # 연노란색
        text_color = '#000000'
    elif status == '진행불가':
        bg_color = '#f8d7da' # 연빨간색
        text_color = '#000000'
    else:
        bg_color = ''
        text_color = ''
    
    if bg_color:
        return [f'background-color: {bg_color}; color: {text_color}; font-weight: bold;'] * len(row)
    else:
        return [''] * len(row)

# --- 4. 메인 프로그램 ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    st.title("🔐 업무 시스템 접속")
    with st.form("login_form"):
        name = st.text_input("성함을 입력하세요")
        if st.form_submit_button("입장하기"):
            if name:
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = name
                st.rerun()
else:
    side_col1, side_col2 = st.sidebar.columns([5, 3], vertical_alignment="center")
    with side_col1:
        st.markdown(f"<p style='font-size: 12px; color: #aaaaaa; margin: 0;'>👤 {st.session_state['user_name']} 님</p>", unsafe_allow_html=True)
    with side_col2:
        if st.button("로그아웃", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.sidebar.divider()
    page_menu = st.sidebar.radio("📌 메뉴 이동", ["📝 팀 업무일지", "⚙️ 장비제작 Flow"])
    st.sidebar.divider()

    # ==========================================
    # PAGE 1: 팀 업무일지 (기존)
    # ==========================================
    if page_menu == "📝 팀 업무일지":
        try:
            df_log, sha_log = get_log_data()
            mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
            # ... (이전과 동일한 업무일지 작성/수정/삭제 로직) ...
            if mode == "➕ 작성":
                with st.sidebar.form("add_form", clear_on_submit=True):
                    d_val = st.date_input("날짜", datetime.today())
                    e_type = st.selectbox("장비", EQUIPMENT_OPTIONS)
                    c_val = st.text_area("업무 내용", height=120)
                    n_val = st.text_input("비고")
                    f_name = st.text_input("파일명 (미입력 시 비워둠)")
                    if st.form_submit_button("저장하기", use_container_width=True):
                        if c_val:
                            full_path = BASE_PATH_RAW + f_name if f_name.strip() else ""
                            new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_path}])
                            save_log_data(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d_val}")
                            st.rerun()
            elif mode == "✏️ 수정":
                if not df_log.empty:
                    edit_idx = st.sidebar.selectbox("대상 선택", options=df_log.index, format_func=lambda x: f"{df_log.iloc[x]['날짜']} | {df_log.iloc[x]['장비']}")
                    with st.sidebar.form("edit_form"):
                        e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[edit_idx, "날짜"]))
                        e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df_log.loc[edit_idx, "장비"]) if df_log.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                        e_content = st.text_area("내용 수정", value=df_log.loc[edit_idx, "업무내용"])
                        e_note = st.text_input("비고 수정", value=df_log.loc[edit_idx, "비고"])
                        e_link = st.text_input("첨부 수정", value=df_log.loc[edit_idx, "첨부"])
                        if st.form_submit_button("수정 완료"):
                            df_log.loc[edit_idx, ["날짜", "장비", "업무내용", "비고", "첨부"]] = [str(e_date), e_etype, e_content, e_note, e_link]
                            save_log_data(df_log, sha_log, f"Edit Log: {e_date}")
                            st.rerun()
            elif mode == "❌ 삭제":
                if not df_log.empty:
                    del_idx = st.sidebar.selectbox("삭제 선택", options=df_log.index, format_func=lambda x: f"{df_log.iloc[x]['날짜']} | {df_log.iloc[x]['장비']}")
                    if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                        save_log_data(df_log.drop(del_idx), sha_log, "Delete Log")
                        st.rerun()

            head_c1, head_c2 = st.columns([5, 1], vertical_alignment="bottom")
            with head_c1: st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
            with head_c2:
                csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button(label="📥 엑셀", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv")

            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            search = st.text_input("🔍 검색", label_visibility="collapsed", placeholder="검색어를 입력하세요...")
            display_df = df_log.copy()
            if search: display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
            st.markdown("<div class='info-box'>📎 <b>사진 확인:</b> 첨부 경로 클릭 → <b>Ctrl+C</b> → <b>[윈도우 키 + R]</b> 에 붙여넣기</div>", unsafe_allow_html=True)

            st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("📝 업무내용", width="large"), "첨부": st.column_config.TextColumn("📎 첨부(클릭복사)")})
        except Exception as e: st.error(f"오류: {e}")

    # ==========================================
    # PAGE 2: 장비제작 (CS Flow) 데이터 에디터
    # ==========================================
    elif page_menu == "⚙️ 장비제작 Flow":
        try:
            df_flow, sha_flow = get_flow_data()
            
            st.markdown("<div class='main-title'>⚙️ CS 작업 체크 시트 (대항목 관리)</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

            project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
            
            # 새 호기(프로젝트) 생성
            with st.expander("➕ 새 프로젝트(호기) 시작하기"):
                with st.form("new_project_form", clear_on_submit=True):
                    new_proj_name = st.text_input("새 프로젝트명 입력 (예: SLH1 #6호기)")
                    if st.form_submit_button("엑셀 템플릿으로 공정표 생성"):
                        if new_proj_name and new_proj_name not in project_list:
                            new_rows = []
                            for item in CS_TEMPLATE:
                                item_copy = item.copy()
                                item_copy["프로젝트명"] = new_proj_name
                                item_copy["업데이트일"] = str(datetime.today().date())
                                new_rows.append(item_copy)
                            df_flow = pd.concat([df_flow, pd.DataFrame(new_rows)], ignore_index=True)
                            save_flow_data(df_flow, sha_flow, f"Create Proj: {new_proj_name}")
                            st.success(f"[{new_proj_name}] CS 작업 시트가 생성되었습니다!")
                            st.rerun()

            if project_list:
                selected_proj = st.selectbox("📌 진행 상황을 확인할 프로젝트 선택", project_list)
                mask = df_flow["프로젝트명"] == selected_proj
                proj_df = df_flow[mask].copy()

                st.markdown("<div class='info-box'>💡 <b>사용 가이드:</b> 각 <b>[대항목]</b> 탭을 눌러 세부작업을 확인하세요. <b>상태(완료,작업중,진행불가)</b>를 변경하면 배경색이 바뀝니다. 사유는 <b>[비고]</b>란에, 사진은 <b>[첨부]</b>란에 입력 후 반드시 하단의 <b>'저장'</b> 버튼을 누르세요.</div>", unsafe_allow_html=True)

                categories = proj_df["대항목"].unique()
                edited_dfs = []

                # 대항목별로 Expander 생성 (아코디언 메뉴)
                for cat in categories:
                    with st.expander(f"📍 대항목: {cat} 작업 리스트", expanded=False):
                        cat_df = proj_df[proj_df["대항목"] == cat]
                        
                        # 배경색을 동적으로 입히기 위해 Pandas Styler 적용
                        styled_df = cat_df.style.apply(highlight_status, axis=1)

                        edited_cat_df = st.data_editor(
                            styled_df,
                            use_container_width=True,
                            hide_index=True,
                            key=f"editor_{selected_proj}_{cat}",
                            column_config={
                                "프로젝트명": None, # 화면에 숨김
                                "대항목": None,    # 이미 탭 이름으로 보여주므로 숨김
                                "순서": st.column_config.NumberColumn("No.", disabled=True, width="small"),
                                "작업내용": st.column_config.TextColumn("📝 세부 작업 내용", disabled=True, width="large"),
                                "상태": st.column_config.SelectboxColumn("상태", options=["대기", "작업중", "완료", "진행불가"], width="small", required=True),
                                "비고": st.column_config.TextColumn("⚠️ 비고 / 보류사유", width="large"),
                                "첨부": st.column_config.TextColumn("📎 첨부(파일명)", width="small"),
                                "업데이트일": st.column_config.TextColumn("수정일", disabled=True)
                            }
                        )
                        edited_dfs.append(edited_cat_df)

                # 전체 저장 버튼
                if st.button("💾 변경된 모든 디테일 저장하기", type="primary", use_container_width=True):
                    updated_proj_df = pd.concat(edited_dfs, ignore_index=True)
                    updated_proj_df["업데이트일"] = str(datetime.today().date())
                    
                    df_flow = df_flow[~mask] # 기존 프로젝트 삭제
                    df_flow = pd.concat([df_flow, updated_proj_df], ignore_index=True) # 업데이트된 데이터 삽입
                    
                    save_flow_data(df_flow, sha_flow, f"Update Flow: {selected_proj}")
                    st.success("✅ 공정 상황이 안전하게 저장되었습니다.")
                    st.rerun()
                
                st.divider()
                
                # 첨부파일 경로 확인용 표
                st.markdown("##### 📁 첨부 파일 FTP 경로 확인")
                full_edited_df = pd.concat(edited_dfs, ignore_index=True)
                file_df = full_edited_df[full_edited_df["첨부"].str.strip() != ""].copy()
                
                if not file_df.empty:
                    file_df["복사할경로"] = BASE_PATH_RAW + file_df["첨부"]
                    st.dataframe(
                        file_df[["작업내용", "복사할경로"]], 
                        use_container_width=True, hide_index=True,
                        column_config={
                            "작업내용": st.column_config.TextColumn("대상 작업", width="medium"),
                            "복사할경로": st.column_config.TextColumn("📎 클릭하여 경로 복사 (Ctrl+C)", width="large")
                        }
                    )
                else:
                    st.caption("입력된 첨부 파일이 없습니다.")
            else:
                st.info("진행 중인 프로젝트가 없습니다. [새 프로젝트 시작하기]를 통해 생성해 주세요.")

        except Exception as e: st.error(f"오류 발생: {e}")
