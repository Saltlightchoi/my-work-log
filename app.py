import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime
import plotly.graph_objects as go  # 📊 그래프를 그리기 위해 추가된 라이브러리

# ==========================================
# 1. 환경 설정 및 기본 상수
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { padding-top: 3rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        div[data-testid="stSidebar"] button[kind="secondary"] { padding: 2px 5px !important; font-size: 12px !important; height: 28px !important; }
        .main-title { font-size: 1.5rem !important; font-weight: bold; margin: 0 !important; padding-bottom: 10px !important; }
        div.stDownloadButton > button { padding: 4px 10px !important; font-size: 12px !important; width: 100% !important; }
        .info-box { background-color: #1e212b; padding: 12px; border-radius: 4px; border-left: 3px solid #4CAF50; margin-bottom: 15px; font-size: 13px; }
        .streamlit-expanderHeader { font-weight: bold !important; font-size: 1.1rem !important; color: #4CAF50 !important; }
        .stProgress > div > div > div > div { background-color: #4CAF50; }
        
        /* 탭 디자인 커스텀 (글씨 크기 및 굵기) */
        button[data-baseweb="tab"] { font-size: 18px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

BASE_PATH_RAW = r"\\192.168.0.100\500 생산\550 국내CS\공유사진\\"
EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

CS_TEMPLATE = [
    {"대항목": "공통", "순서": 1, "작업내용": "I/O Check\n- Out Put으로 동작 후 In Put LED 확인\n- Cylinder 정상 동작 확인\n- Manual에서 Cylinder 동작 후 LED 점등 확인\n- 미비된 부분 I/O List, PC에 저장 후 전장 수정 요청 진행\n- 전장 수정 후 수정되었는지 동작, LED 확인", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 2, "작업내용": "공압 Leak Check", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 3, "작업내용": "Cylinder Speed 조정 및 Part 위치 조정", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 4, "작업내용": "전면부 후면부 1차 Levelling\n- Auto Leveler 사용\n- Stacker Base 상단 -> 바닥면 400mm", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Stacker", "순서": 1, "작업내용": "L/D 1,2, UL/D 1,2, Emt, Reject Inverter 값 설정\n- 운전 모드 변경 P79-2(인터락 해제), P79-1(인터락 작동)\n- P3: 60, P4: 60(고속), P5: 30(중속), P6: 10(저속), P7: 5(가속), P8: 0(감속)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 1, "작업내용": "Motor Parameter Setting 및 다회전 클리어\n- S/W 팀 요청\n- 다회전 클리어 방법: Panaterm Ver.6.0 다운 후 해당 Parameter Servo Drive에 케이블 연결 -> 앰프 접속 -> 확인 -> 모니터 -> 다회전 클리어 클릭 -> 완료", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 2, "작업내용": "Precizer Up Rod 길이 변경 (57mm)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Hand", "순서": 1, "작업내용": "Loader Unloader X,Y축 직진도 (±0.5mm) Setting 및 측정\n- Dial Gauge Indicator 0.01mm(바늘)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Hand", "순서": 2, "작업내용": "L/D, UL/D Pitch, 높이(±0.15mm) Setting 및 측정\n- Dial Gauge Indicator 0.01mm(바늘)\n- Double Nut로 길이 조정", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Stacker", "순서": 1, "작업내용": "L/D 1,2, UL/D 1,2, Empty, Reject Base 평탄도(±0.2mm) Setting 및 측정\n- 디지털 전자 수평계 사용 X,Y축 ±0.2mm 이내", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Transfer", "순서": 1, "작업내용": "L/D, UL/D X,Y,Z축 직진도 평탄도(±0.3mm) Setting 및 측정\n- Dial Gauge Indicator 0.01mm(바늘)\n- 모든 무두 볼트 풀어놓은 후 측정 후 무드 볼트 조정\n- Z축 ±Limit Sensor 이동, Hard Stopper 위치변경", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Test", "순서": 1, "작업내용": "Front, Rear Press 평탄도(±0.25mm) Setting 및 측정\n- 디지털 거리 측정기, 측정 지그 사용\n- 무두 볼트 풀어놓은 후 측정 -> + 수치가 제일 큰 부분에 리셋 -> 무두 볼트 사용하여 평탄도 Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Test", "순서": 2, "작업내용": "Front, Rear Press Load Cell (0.2bar, 0.29bar) Setting 및 측정\n- Load Cell, 측정 지그\n- 언 컨텍 값(기구 이동 가능), 컨택값(해당 수치 도달 지점)\n- Load Cell 로드를 Match Plate X,Y 중간에서 컨택 해야함", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Test", "순서": 3, "작업내용": "Front, Rear T-Tray Rail 평탄도(±0.2mm) Setting 및 측정\n- 디지털 전자 수평계 사용\n- 측정 위치 : T-Tray 왼쪽 중간 오른쪽", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Set Plate", "순서": 1, "작업내용": "L/D 1,2, UL/D 1,2 X축 직진도(±0.2mm) (Gauge Block 사용) 평탄도(±0.2mm) Setting 및 측정\n- Dial Gauge Indicator 0.01mm(바늘)\n- Gauge Block 사용", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Stacker", "순서": 1, "작업내용": "Reject Front Rear Base 높이 조정\n- Rear Base Cylinder Rod 최대로 내린뒤, Front를 무두 볼트 사용하여 Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Set Plate", "순서": 1, "작업내용": "L/D 1,2, UL/D 1,2 Support Lock/Unlock Cylinder Rod Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Set Plate", "순서": 2, "작업내용": "L/D 1,2, UL/D 1,2 Down Hard Stopper 높이 Setting (24mm) 및 측정\n- Ex) L/D 1,2: 21mm, UL/D 1,2: 24mm Pass", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Middle", "순서": 1, "작업내용": "L/D, UL/D Gripper Up Cylinder Rod (37mm) Setting\n- Cylinder 상단에서 Joint Nut 상단 까지 37mm Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Input", "순서": 1, "작업내용": "Bottom Feeder Up Cylinder Rod (16.5mm) Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Output", "순서": 1, "작업내용": "Bottom Feeder Up Cylinder Rod (16.5mm) Setting", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 1, "작업내용": "전면부 후면부 Docking 및 Levelling\n- Auto Leveler 사용\n- Stacker Base 상단 -> 바닥면 400mm -> 전면부 풋 높이랑 동일하게 후면부 Setting\n- 전면부 Levelling -> Docking Pin 제거, 전면부 Cable Disconnect -> 후면부랑 전면부 Docking -> 후면부 Levelling -> Docking Pin 장착(안맞으면 빠루로 좌,우 이동) -> Cable Connect", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Middle", "순서": 1, "작업내용": "L/D, UL/D Rail Up/Down 높이, 평탄, 직진도 Setting (T-Tray 사용)\n- T-Tray 사용, Up/Down 상태에서 T-Tray가 흘려 내려가지 않게 Setting\n- Stopper 사용하여 Up/Down 높이 레벨 조정 (Up: 48.5mm, Down: 42.5mm)\n- Up 상태일때 후면부 Rail 한쪽이 안맞는다면 후면부 쪽 Rail 위치 조정 필요", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 1, "작업내용": "배출 Fan 장착 및 전원 Connect 연결\n- I/O 번호 확인, OS에서 Fan Check 확인", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Hand", "순서": 1, "작업내용": "L/D, UL/D X,Y축 반복도(±0.05mm) 측정 (10회)\n- Dial Gauge Indicator 0.01mm(바늘)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Transfer", "순서": 1, "작업내용": "L/D, UL/D X,Z축 반복도(±0.05mm) 측정 (10회)\n- Digital Indicator (0.001mm) 사용", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "Input", "순서": 1, "작업내용": "Bottom Feeder X축 반복도(±0.05mm) 측정 (10회)\n- Dial Gauge Indicator 0.01mm(바늘)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 1, "작업내용": "Transfer, Hand, Middle Feeder, Input, Output Motor Teaching", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 2, "작업내용": "후면부 덕트 -> 측면(Door) -> 후면(Door) -> 상부 Cover 장착 -> 부속 Cover 장착, Door Key, Door Sensor 장착 및 OS 확인", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 3, "작업내용": "Ionizer Loader A-01, Unloader A-02 설정", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 4, "작업내용": "접지 연결 및 확인", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 5, "작업내용": "환경 검수 List 확인 및 품질팀 Support", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 6, "작업내용": "Initial 및 Long Run 진행 (T-Tray 미사용)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 7, "작업내용": "Dry Run 진행 (T-Tray 사용)", "상태": "⬜ 대기", "비고": "", "첨부": ""},
    {"대항목": "공통", "순서": 8, "작업내용": "Dummy Run 진행 및 Clear Alarm (3000회)", "상태": "⬜ 대기", "비고": "", "첨부": ""}
]

# ==========================================
# 2. 데이터 관리 공장
# ==========================================
class DataManager:
    def __init__(self, repo, file_path, text_columns):
        self.repo = repo
        self.file_path = file_path
        self.text_columns = text_columns

    def load(self):
        try:
            file_content = self.repo.get_contents(self.file_path)
            df = pd.read_csv(io.StringIO(file_content.decoded_content.decode('utf-8-sig')))
            df = df.loc[:, ~df.columns.duplicated()]
            for col in self.text_columns:
                if col not in df.columns: df[col] = ""
                else: df[col] = df[col].fillna("").astype(str)
            return df, file_content.sha
        except:
            return pd.DataFrame(columns=self.text_columns), None

    def save(self, df, sha, message):
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
        if sha: self.repo.update_file(self.file_path, message, csv_buffer.getvalue(), sha)
        else: self.repo.create_file(self.file_path, "Init Creation", csv_buffer.getvalue())

def maintain_project_order(df, original_order):
    df['__proj_cat__'] = pd.Categorical(df['프로젝트명'], categories=original_order, ordered=True)
    return df.sort_values(by=['__proj_cat__'], kind='stable').drop(columns=['__proj_cat__']).reset_index(drop=True)

def get_row_color(row):
    val = row.get('상태', '')
    if val == '✅ 완료': return ['background-color: rgba(76, 175, 80, 0.2)'] * len(row)
    elif val == '⏳ 작업중': return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
    elif val == '🚨 보류': return ['background-color: rgba(244, 67, 54, 0.2)'] * len(row)
    return [''] * len(row)

# ==========================================
# 3. 화면 UI 보따리 (탭 1: 업무일지)
# ==========================================
def render_work_log_page(db_log):
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"], key="log_mode_select")
    
    if mode == "➕ 작성":
        with st.sidebar.form("add_form", clear_on_submit=True):
            d_val = st.date_input("날짜", datetime.today())
            e_type = st.selectbox("장비", EQUIPMENT_OPTIONS)
            c_val = st.text_area("업무 내용", height=400, max_chars=None)
            n_val = st.text_input("비고")
            f_name = st.text_input("파일명 (미입력 시 비워둠)")
            if st.form_submit_button("저장하기", use_container_width=True):
                if c_val:
                    full_path = BASE_PATH_RAW + f_name if f_name.strip() else ""
                    new_row = pd.DataFrame([{"날짜": str(d_val), "장비": e_type, "작성자": st.session_state['user_name'], "업무내용": c_val, "비고": n_val, "첨부": full_path}])
                    db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d_val}")
                    st.rerun()

    elif mode == "✏️ 수정":
        if not df_log.empty:
            edit_idx = st.sidebar.selectbox("대상 선택", options=df_log.index, format_func=lambda x: f"{df_log.iloc[x]['날짜']} | {df_log.iloc[x]['장비']} | {str(df_log.iloc[x]['업무내용'])[:15]}...")
            with st.sidebar.form("edit_form"):
                e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[edit_idx, "날짜"]))
                e_etype = st.selectbox("장비 수정", EQUIPMENT_OPTIONS, index=EQUIPMENT_OPTIONS.index(df_log.loc[edit_idx, "장비"]) if df_log.loc[edit_idx, "장비"] in EQUIPMENT_OPTIONS else 0)
                e_content = st.text_area("내용 수정", value=df_log.loc[edit_idx, "업무내용"], height=400, max_chars=None)
                e_note = st.text_input("비고 수정", value=df_log.loc[edit_idx, "비고"])
                e_link = st.text_input("첨부 수정", value=df_log.loc[edit_idx, "첨부"])
                if st.form_submit_button("수정 완료"):
                    df_log.loc[edit_idx, ["날짜", "장비", "업무내용", "비고", "첨부"]] = [str(e_date), e_etype, e_content, e_note, e_link]
                    db_log.save(df_log, sha_log, f"Edit Log: {e_date}")
                    st.rerun()

    elif mode == "❌ 삭제":
        if not df_log.empty:
            del_idx = st.sidebar.selectbox("삭제 선택", options=df_log.index, format_func=lambda x: f"{df_log.iloc[x]['날짜']} | {df_log.iloc[x]['장비']} | {str(df_log.iloc[x]['업무내용'])[:15]}...")
            selected_row = df_log.iloc[del_idx]
            st.sidebar.markdown("### ⚠️ 삭제 대상 상세 정보")
            st.sidebar.info(f"**📅 날짜:** {selected_row['날짜']}\n\n**⚙️ 장비:** {selected_row['장비']}\n\n**👤 작성자:** {selected_row['작성자']}\n\n**📝 업무내용:**\n{selected_row['업무내용']}\n\n**📌 비고:** {selected_row['비고']}")
            if st.sidebar.button("🗑️ 최종 삭제 (복구 불가)", use_container_width=True):
                db_log.save(df_log.drop(del_idx), sha_log, "Delete Log")
                st.rerun()

    # 기존에 있던 페이지 이동 버튼 제거 완료
    col_title, col_excel = st.columns([8.5, 1.5])
    with col_title:
        st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    with col_excel:
        csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 엑셀 다운로드", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    search = st.text_input("🔍 검색", label_visibility="collapsed", placeholder="검색어를 입력하세요...")
    display_df = df_log.copy()
    if search: display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("📝 업무내용", width="large"), "첨부": st.column_config.TextColumn("📎 첨부(클릭복사)")})

# ==========================================
# 3. 화면 UI 보따리 (탭 2: CS 작업체크시트)
# ==========================================
def render_cs_flow_page(db_flow):
    df_flow, sha_flow = db_flow.load()
    
    # 기존에 있던 페이지 이동 버튼 제거 완료
    st.markdown("<div class='main-title'>✅ CS 작업 체크 시트 (대항목 관리)</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
    
    if 'current_proj' not in st.session_state:
        st.session_state['current_proj'] = project_list[0] if project_list else ""
    if st.session_state['current_proj'] not in project_list:
        st.session_state['current_proj'] = project_list[0] if project_list else ""
    
    progress_dict = {}
    if not df_flow.empty:
        for proj in project_list:
            p_df = df_flow[df_flow["프로젝트명"] == proj]
            total_items = len(p_df)
            completed_items = len(p_df[p_df["상태"] == "✅ 완료"])
            pct = int((completed_items / total_items) * 100) if total_items > 0 else 0
            
            blocks = pct // 10
            bar = "🟩" * blocks + "⬜" * (10 - blocks)
            batt_icon = "🔋" if pct >= 20 else "🪫"
            progress_dict[proj] = f"{proj}  |  {batt_icon} {pct}% [{bar}]"

    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("➕ 새 프로젝트(호기) 시작하기"):
            with st.form("new_proj_form", clear_on_submit=True):
                new_proj = st.text_input("새 프로젝트명 (예: SLH1 #7호기)")
                source_options = ["기본 템플릿(초기화 상태)"] + project_list
                
                def format_source_opt(x):
                    return progress_dict.get(x, x)
                source_proj = st.selectbox("어떤 형식과 내용을 복사해서 생성할까요?", source_options, format_func=format_source_opt)

                if st.form_submit_button("프로젝트 생성하기") and new_proj and new_proj not in project_list:
                    if source_proj == "기본 템플릿(초기화 상태)":
                        new_df = pd.DataFrame(CS_TEMPLATE)
                    else:
                        new_df = df_flow[df_flow["프로젝트명"] == source_proj].copy()
                        new_df["상태"] = "⬜ 대기"
                        new_df["비고"] = ""
                        new_df["첨부"] = ""
                        new_df["업데이트일"] = ""

                    new_df["프로젝트명"] = new_proj
                    
                    new_df['group_id'] = (new_df['대항목'] != new_df['대항목'].shift()).cumsum()
                    unique_names = {}
                    counts = {}
                    for gid in new_df['group_id'].unique():
                        cat = new_df.loc[new_df['group_id'] == gid, '대항목'].iloc[0]
                        base_cat = cat.split(" (")[0] if " (" in cat else cat 
                        
                        if base_cat not in counts:
                            counts[base_cat] = 1
                            unique_names[gid] = base_cat
                        else:
                            counts[base_cat] += 1
                            unique_names[gid] = f"{base_cat} ({counts[base_cat]})"
                            
                    new_df['대항목'] = new_df['group_id'].map(unique_names)
                    new_df["순서"] = new_df.groupby('group_id').cumcount() + 1
                    
                    db_flow.save(pd.concat([df_flow, new_df.drop(columns=['group_id'])], ignore_index=True), sha_flow, f"Create: {new_proj}")
                    st.session_state['current_proj'] = new_proj
                    st.rerun()

    if project_list:
        sel_col, empty_col, save_col, del_col = st.columns([6, 2, 1, 1])
        default_idx = project_list.index(st.session_state['current_proj']) if project_list else 0
        
        with sel_col: 
            selected_proj = st.selectbox(
                "📌 진행 상황 확인할 프로젝트", 
                project_list, 
                index=default_idx,
                format_func=lambda x: progress_dict.get(x, x)
            )
            st.session_state['current_proj'] = selected_proj 
            
        with save_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_save = st.button("💾 저장", use_container_width=True)
            
        with del_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ 삭제", use_container_width=True):
                st.session_state['delete_target_proj'] = selected_proj
                st.rerun()

        mask = df_flow["프로젝트명"] == selected_proj
        proj_df = df_flow[mask].copy()

        if st.session_state.get('delete_target_proj') == selected_proj:
            st.markdown(f"""
                <div style='background-color: #ffebee; border-left: 5px solid #f44336; padding: 15px; border-radius: 4px; margin-bottom: 15px;'>
                    <h3 style='color: #d32f2f; margin-top: 0;'>🚨 프로젝트 영구 삭제 경고</h3>
                    <p style='color: #000; font-size: 15px;'><b>[{selected_proj}]</b> 프로젝트를 삭제하시겠습니까?<br>
                    이 작업은 <b>절대 복구할 수 없으며</b>, 기록된 모든 세부 작업과 메모가 즉시 영구 삭제됩니다.</p>
                </div>
            """, unsafe_allow_html=True)
            
            agree_delete = st.checkbox("네, 복구가 불가능하다는 것을 확인했으며 모두 삭제하는 것에 동의합니다.")
            
            conf_col1, conf_col2 = st.columns(2)
            with conf_col1:
                if agree_delete:
                    if st.button("⚠️ 모든 것을 지우고 완전히 삭제합니다", type="primary", use_container_width=True):
                        db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
                        st.session_state['delete_target_proj'] = None
                        st.session_state['current_proj'] = project_list[0] if len(project_list) > 1 else ""
                        st.success("🗑️ 프로젝트가 완전히 삭제되었습니다.")
                        st.rerun()
                else:
                    st.button("⚠️ 위 체크박스에 동의해야 삭제할 수 있습니다", disabled=True, use_container_width=True)
                    
            with conf_col2:
                if st.button("❌ 아니오, 취소합니다 (돌아가기)", use_container_width=True):
                    st.session_state['delete_target_proj'] = None
                    st.rerun()
            st.stop() 

        total_tasks = len(proj_df)
        comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
        pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
        pct_int = int(pct_float * 100)
        
        st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#4CAF50;'>⚡ 셋업 전체 진행도 ({comp_tasks} / {total_tasks} 완료)</div>", unsafe_allow_html=True)
        st.progress(pct_float, text=f"전체 {pct_int}% 완료됨")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        with col_b:
            with st.expander("📁 대항목(그룹) 관리 메뉴"):
                tab_add, tab_ren, tab_ord, tab_del = st.tabs(["➕ 추가", "✏️ 이름 변경", "↕️ 순서 변경", "🗑️ 삭제"])
                
                existing_cats = []
                for c in proj_df['대항목']:
                    if c not in existing_cats: existing_cats.append(c)
                
                with tab_add:
                    with st.form("new_cat_form", clear_on_submit=True):
                        new_cat_name = st.text_input("추가할 그룹명 (예: Packing)")
                        if st.form_submit_button("새 그룹 생성") and new_cat_name:
                            final_cat_name = new_cat_name
                            counter = 2
                            while final_cat_name in existing_cats:
                                final_cat_name = f"{new_cat_name} ({counter})"
                                counter += 1
                                
                            new_cat_row = pd.DataFrame([{
                                "프로젝트명": selected_proj, "대항목": final_cat_name, "순서": 1,
                                "작업내용": "신규 작업 내용을 입력하세요", "상태": "⬜ 대기",
                                "비고": "", "첨부": "", "업데이트일": ""
                            }])
                            
                            original_projects = df_flow['프로젝트명'].unique().tolist()
                            new_df_flow = pd.concat([df_flow, new_cat_row], ignore_index=True)
                            new_df_flow = maintain_project_order(new_df_flow, original_projects) 
                            db_flow.save(new_df_flow, sha_flow, f"Add Cat: {final_cat_name}")
                            st.rerun()

                with tab_ren:
                    with st.form("rename_cat_form", clear_on_submit=True):
                        old_cat_name = st.selectbox("이름을 바꿀 대항목 선택", existing_cats)
                        renamed_cat_name = st.text_input("변경할 새로운 이름 입력")
                        if st.form_submit_button("이름 변경 적용") and renamed_cat_name:
                            final_renamed = renamed_cat_name
                            counter = 2
                            while final_renamed in existing_cats and final_renamed != old_cat_name:
                                final_renamed = f"{renamed_cat_name} ({counter})"
                                counter += 1
                                
                            df_flow.loc[(df_flow['프로젝트명'] == selected_proj) & (df_flow['대항목'] == old_cat_name), '대항목'] = final_renamed
                            db_flow.save(df_flow, sha_flow, f"Rename Cat: {old_cat_name} -> {final_renamed}")
                            st.success(f"[{old_cat_name}]이(가) [{final_renamed}](으)로 변경되었습니다!")
                            st.rerun()
                
                with tab_ord:
                    st.markdown("<p style='font-size:13px; color:#aaa;'>💡 표의 숫자를 원하는 순서로 수정한 뒤 아래 [순서 적용] 버튼을 누르세요.</p>", unsafe_allow_html=True)
                    cat_order_df = pd.DataFrame({"대항목": existing_cats, "순서": range(1, len(existing_cats) + 1)})
                    edited_cat_order = st.data_editor(
                        cat_order_df, 
                        hide_index=True, 
                        use_container_width=True,
                        disabled=["대항목"],
                        column_config={"순서": st.column_config.NumberColumn("위치(순서) 변경", step=1)}
                    )
                    if st.button("순서 변경 적용", use_container_width=True):
                        new_order_list = edited_cat_order.sort_values(by="순서")["대항목"].tolist()
                        temp_proj_df = df_flow[mask].copy()
                        temp_proj_df['대항목'] = pd.Categorical(temp_proj_df['대항목'], categories=new_order_list, ordered=True)
                        temp_proj_df = temp_proj_df.sort_values(by=['대항목', '순서'])
                        temp_proj_df['대항목'] = temp_proj_df['대항목'].astype(str)
                        temp_proj_df['group_id'] = (temp_proj_df['대항목'] != temp_proj_df['대항목'].shift()).cumsum()
                        temp_proj_df["순서"] = temp_proj_df.groupby('group_id').cumcount() + 1
                        temp_proj_df = temp_proj_df.drop(columns=['group_id']).reset_index(drop=True)
                        
                        original_projects = df_flow['프로젝트명'].unique().tolist()
                        new_df_flow = pd.concat([df_flow[~mask], temp_proj_df], ignore_index=True)
                        new_df_flow = maintain_project_order(new_df_flow, original_projects) 
                        
                        db_flow.save(new_df_flow, sha_flow, f"Reorder Cats: {selected_proj}")
                        st.success("✅ 대항목 순서가 성공적으로 변경되었습니다!")
                        st.rerun()

                with tab_del:
                    with st.form("delete_cat_form", clear_on_submit=True):
                        del_cat_name = st.selectbox("삭제할 대항목(그룹) 선택", existing_cats)
                        st.error("⚠️ 주의: 해당 그룹을 삭제하면 안에 있는 모든 세부 작업 내용도 함께 영구 삭제됩니다!")
                        confirm_del = st.checkbox("네, 일부 그룹만 삭제하는 것에 동의합니다.")
                        if st.form_submit_button("그룹 완전히 삭제하기"):
                            if confirm_del and del_cat_name:
                                df_flow = df_flow[~((df_flow['프로젝트명'] == selected_proj) & (df_flow['대항목'] == del_cat_name))]
                                db_flow.save(df_flow, sha_flow, f"Delete Cat: {del_cat_name}")
                                st.success(f"[{del_cat_name}] 그룹이 성공적으로 삭제되었습니다!")
                                st.rerun()
                            elif not confirm_del:
                                st.warning("삭제를 진행하시려면 체크박스에 동의해주세요.")
        
        st.markdown("<div class='info-box'>💡 <b>편집 가이드:</b> 상태를 변경하고 우측 상단의 <b>'💾 저장'</b> 버튼을 누르면 <b>색상이 적용</b>되며 탭의 상태 아이콘(🟢🟡🔴)도 자동 갱신됩니다!</div>", unsafe_allow_html=True)

        status_options = ["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"]
        custom_column_config = {
            "프로젝트명": None, 
            "대항목": None,
            "순서": st.column_config.NumberColumn("No(순서수정)", disabled=False, width="small"), 
            "작업내용": st.column_config.TextColumn("📝 세부 작업 내용", width="large"), 
            "상태": st.column_config.SelectboxColumn("상태", options=status_options, width="small", required=True), 
            "비고": st.column_config.TextColumn("⚠️ 비고 / 보류사유", width="large"),
            "업데이트일": st.column_config.TextColumn("수정자 & 수정일", disabled=True, width="small"), 
            "첨부": st.column_config.TextColumn("📎 첨부", width="small")
        }

        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        groups = proj_df.groupby('group_id', sort=False) 
        
        edited_dfs = []
        current_user_stamp = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"

        for group_id, group_df in groups:
            cat = group_df['대항목'].iloc[0]
            display_df = group_df.drop(columns=['group_id']).reset_index(drop=True)
            
            current_statuses = display_df['상태'].tolist()
            
            if '🚨 보류' in current_statuses:
                tab_title = f"🔴 [보류발생] 대항목: {cat}"
            elif current_statuses and all(s == '✅ 완료' for s in current_statuses):
                tab_title = f"🟢 [완료] 대항목: {cat}"
            elif '⏳ 작업중' in current_statuses or '✅ 완료' in current_statuses:
                tab_title = f"🟡 [진행중] 대항목: {cat}"
            else:
                tab_title = f"📍 [대기] 대항목: {cat}"
            
            with st.expander(tab_title, expanded=False):
                styled_df = display_df.style.apply(get_row_color, axis=1)
                
                edited_cat_df = st.data_editor(
                    styled_df,
                    use_container_width=True, 
                    hide_index=True, num_rows="dynamic",
                    key=f"editor_{selected_proj}_{group_id}",
                    column_config=custom_column_config,
                    column_order=["순서", "작업내용", "상태", "비고", "업데이트일", "첨부"] 
                )
                
                for idx, new_row in edited_cat_df.iterrows():
                    if new_row['상태'] == "⬜ 대기":
                        edited_cat_df.at[idx, '업데이트일'] = ""
                    else:
                        match = display_df[
                            (display_df['작업내용'] == new_row['작업내용']) &
                            (display_df['상태'] == new_row['상태']) &
                            (display_df['비고'] == new_row['비고']) &
                            (display_df['첨부'] == new_row['첨부']) &
                            (display_df['순서'] == new_row['순서'])
                        ]
                        if match.empty:
                            edited_cat_df.at[idx, '업데이트일'] = current_user_stamp
                        else:
                            edited_cat_df.at[idx, '업데이트일'] = match.iloc[0]['업데이트일']
                
                edited_cat_df["대항목"] = cat
                edited_cat_df["프로젝트명"] = selected_proj
                edited_cat_df["org_group_id"] = group_id 
                edited_dfs.append(edited_cat_df)

        if btn_save:
            updated_proj_df = pd.concat(edited_dfs, ignore_index=True)
            if not updated_proj_df.empty:
                updated_proj_df = updated_proj_df.sort_values(by=['org_group_id', '순서'], kind='stable')
                updated_proj_df['group_id'] = (updated_proj_df['대항목'] != updated_proj_df['대항목'].shift()).cumsum()
                updated_proj_df["순서"] = updated_proj_df.groupby('group_id').cumcount() + 1
                updated_proj_df = updated_proj_df.drop(columns=['group_id', 'org_group_id']).reset_index(drop=True)
            
            original_projects = df_flow['프로젝트명'].unique().tolist()
            new_df_flow = pd.concat([df_flow[~mask], updated_proj_df], ignore_index=True)
            new_df_flow = maintain_project_order(new_df_flow, original_projects) 
            
            db_flow.save(new_df_flow, sha_flow, f"Update: {selected_proj}")
            st.session_state['current_proj'] = selected_proj 
            st.success("✅ 변경사항 및 상태가 성공적으로 저장되었습니다.")
            st.rerun()

    else:
        st.info("진행 중인 프로젝트가 없습니다.")

# ==========================================
# 4. 화면 UI 보따리 (★ 탭 3: 데이터 정합성 및 화면 출력 오류 최종 해결본)
# ==========================================
def render_equipment_data_page():
    # 1. CSS 스타일 정의 (진한 검정색 테두리와 고정 너비)
    st.markdown("""
        <style>
            .fixed-table-container { width: 100%; overflow-x: auto; }
            .fixed-table-container table {
                width: 100%; border-collapse: collapse; border: 2px solid #000000 !important;
                font-size: 13px; color: #000000;
            }
            .fixed-table-container th, .fixed-table-container td {
                border: 1px solid #000000 !important; padding: 6px; text-align: center !important;
            }
            .fixed-table-container th { background-color: #d9e1f2 !important; font-weight: bold; }
            .fixed-table-container td:nth-child(4), .fixed-table-container td:nth-child(5) { text-align: left !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>📊 장비 가동 데이터 (Unit/Jam/PPJ 통합 분석)</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: equipment = st.selectbox("장비 선택", EQUIPMENT_OPTIONS, key="eq_data_equip")
    with col2: unit = st.selectbox("호기 선택", ["1호기", "2호기", "3호기", "4호기", "5호기"], key="eq_data_unit")
    with col3: month_str = st.selectbox("조회할 월 선택", ["1월", "2월", "3월"], key="eq_data_month")

    file_map = {"1월": "SLH1 - January 2026.xlsx", "2월": "SLH1 - February 2026.xlsx", "3월": "SLH1 - March 2026.xlsx"}
    target_file = file_map.get(month_str, "")
    month_num = month_str.replace("월", "")

    try:
        xls = pd.read_excel(target_file, sheet_name=None, header=None, engine='openpyxl')
        df_raw = None
        for name, data in xls.items():
            if data.astype(str).apply(lambda r: r.str.contains('Total Unit', case=False).any(), axis=1).any():
                df_raw = data; break
        
        if df_raw is None:
            st.error("⚠️ 가동 데이터 시트를 찾을 수 없습니다."); return

        # [1. 요약 데이터 추출 및 3축 그래프]
        def get_sum_row(k_list):
            for _, r in df_raw.iterrows():
                row_str = "".join(r.astype(str)).lower().replace(" ", "")
                if any(k in row_str for k in k_list) and not any(x in row_str for x in ['%', '발생률']):
                    vals = r.tolist()
                    for i, v in enumerate(vals):
                        if str(v).replace('.','').replace(',','').strip().isdigit(): return (vals[i:i+31]+[0]*31)[:31]
            return [0]*31

        units = get_sum_row(['totalunit'])
        jams = get_sum_row(['jamcount'])
        ppjs = get_sum_row(['ppj'])

        chart_df = pd.DataFrame({'날짜': [f"{month_num}/{i}" for i in range(1, 32)], 'Unit': units, 'Jam': jams, 'PPJ': ppjs})
        for c in ['Unit', 'Jam', 'PPJ']:
            chart_df[c] = pd.to_numeric(chart_df[c].astype(str).str.replace(',', '').replace(['nan','비가동','미가동','None',''], '0'), errors='coerce').fillna(0)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=chart_df['날짜'], y=chart_df['Unit'], name='투입량(Unit)', marker_color='#5B9BD5', yaxis='y1'))
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['Jam'], name='에러(Jam)', mode='lines+markers', line=dict(color='#ED7D31', width=2), yaxis='y2'))
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['PPJ'], name='효율(PPJ)', mode='lines+markers', line=dict(color='#70AD47', width=2, dash='dot'), yaxis='y3'))
        fig.update_layout(height=400, xaxis=dict(tickangle=-45), 
            yaxis=dict(title=dict(text="Unit", font=dict(color="#5B9BD5")), tickfont=dict(color="#5B9BD5")),
            yaxis2=dict(title=dict(text="Jam", font=dict(color="#ED7D31")), tickfont=dict(color="#ED7D31"), overlaying="y", side="right"),
            yaxis3=dict(title=dict(text="PPJ", font=dict(color="#70AD47")), tickfont=dict(color="#70AD47"), overlaying="y", side="right", anchor="free", position=0.93),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=50, r=120, t=50, b=50), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        # [2. 상세 내역 데이터 정제]
        st.subheader(f"📋 {month_str} 에러 상세 분석 리스트")
        h_idx = -1
        for i, row in df_raw.iterrows():
            if 'error code' in " ".join(row.astype(str)).lower():
                h_idx = i; h_row = row.tolist(); break

        if h_idx != -1:
            col_pos = {'날짜': 0, '에러코드': 0, '에러내용': 0, '조치내용': 0, '시간': 0, '위치': 0, 'PPJ': 0}
            for i, v in enumerate(h_row):
                v_l = str(v).lower().strip()
                if 'date' in v_l: col_pos['날짜'] = i
                elif 'error code' in v_l: col_pos['에러코드'] = i
                elif 'error massage' in v_l: col_pos['에러내용'] = i
                elif 'finding/action' in v_l: col_pos['조치내용'] = i
                elif 'err. time' in v_l: col_pos['시간'] = i
                elif 'err. point' in v_l: col_pos['위치'] = i
                elif 'ppj' in v_l: col_pos['PPJ'] = i

            data_slice = df_raw.iloc[h_idx + 1:].copy()
            cleaned_rows = []
            
            for _, r in data_slice.iterrows():
                code_val = str(r[col_pos['에러코드']]).strip()
                if code_val in ['nan', 'None', '']: continue
                
                # 날짜 및 PPJ (Forward Fill 로직 포함)
                dt = r[col_pos['날짜']]
                if pd.isna(dt) or str(dt).strip() == 'nan': dt = None
                elif str(dt).replace('.','').isdigit():
                    dt = pd.to_datetime(float(dt), unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
                else: dt = str(dt).split(' ')[0]

                ppj_val = str(r[col_pos['PPJ']]).split('.')[0] if not pd.isna(r[col_pos['PPJ']]) else None

                cleaned_rows.append({
                    "날짜": dt, "에러코드": code_val, "PPJ": ppj_val,
                    "에러내용": str(r[col_pos['에러내용']]), "조치내용": str(r[col_pos['조치내용']]),
                    "시간": str(r[col_pos['시간']]).split('.')[0], "위치": str(r[col_pos['위치']])
                })

            if cleaned_rows:
                final_df = pd.DataFrame(cleaned_rows)
                final_df['날짜'] = final_df['날짜'].ffill()
                final_df['PPJ'] = final_df['PPJ'].ffill().fillna("0")
                
                # HTML 테이블 생성 (데이터 밀림 방지 위해 DataFrame에서 바로 변환)
                table_html = final_df.to_html(index=False, border=0, classes='final-report-table')
                st.markdown(f'<div class="fixed-table-container">{table_html}</div>', unsafe_allow_html=True)
            else: st.info("기록된 상세 에러 내역이 없습니다.")
        else: st.info("데이터 헤더를 찾을 수 없습니다.")

    except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")
        
# ==========================================
# 5. 메인 실행 (Main App) - 탭 구조로 변경됨!
# ==========================================
def main():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 연결 설정 오류: {e}")
        return

    # 기존의 current_page 세션 관리는 탭 사용으로 인해 더 이상 필요하지 않아 제거했습니다.

    if 'logged_in' not in st.session_state: 
        st.session_state.update({'logged_in': False, 'user_name': ""})
    
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            name = st.text_input("성함을 입력하세요")
            if st.form_submit_button("입장하기") and name:
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        st.sidebar.markdown(f"👤 **{st.session_state['user_name']}** 님 환영합니다.")
        if st.sidebar.button("로그아웃"): 
            st.session_state['logged_in'] = False
            st.rerun()
        
        # ★ 핵심 변경 사항: 항상 상단에 보이도록 3개의 탭 생성
        tab1, tab2, tab3 = st.tabs(["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터"])
        
        with tab1:
            render_work_log_page(db_log)
        with tab2:
            render_cs_flow_page(db_flow)
        with tab3:
            render_equipment_data_page()

if __name__ == "__main__":
    main()






















