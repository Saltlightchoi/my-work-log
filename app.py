import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime

# ==========================================
# 1. 환경 설정 및 기본 상수 (Constants)
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
    </style>
    """, unsafe_allow_html=True)

BASE_PATH_RAW = r"\\192.168.0.100\500 생산\550 국내CS\공유사진\\"
EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# 35개 CS 항목 템플릿
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
# 2. 데이터 관리 공장 (Class Definition)
# ==========================================
class DataManager:
    """GitHub CSV 파일을 불러오고 저장하는 전용 클래스"""
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


# ==========================================
# 3. 화면 UI 보따리 (Functions)
# ==========================================
def render_work_log_page(db_log):
    """팀 업무일지 화면을 그려주는 함수"""
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

    mode = st.sidebar.selectbox("작업 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
    
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
                    db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d_val}")
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
                    db_log.save(df_log, sha_log, f"Edit Log: {e_date}")
                    st.rerun()

    elif mode == "❌ 삭제":
        if not df_log.empty:
            del_idx = st.sidebar.selectbox("삭제 선택", options=df_log.index, format_func=lambda x: f"{df_log.iloc[x]['날짜']} | {df_log.iloc[x]['장비']}")
            if st.sidebar.button("🗑️ 최종 삭제", use_container_width=True):
                db_log.save(df_log.drop(del_idx), sha_log, "Delete Log")
                st.rerun()

    # 대시보드 출력부
    head_c1, head_c2 = st.columns([5, 1])
    with head_c1: st.markdown("<div class='main-title'>📊 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    with head_c2:
        csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 엑셀", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv")

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    search = st.text_input("🔍 검색", label_visibility="collapsed", placeholder="검색어를 입력하세요...")
    display_df = df_log.copy()
    if search: display_df = display_df[display_df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("📝 업무내용", width="large"), "첨부": st.column_config.TextColumn("📎 첨부(클릭복사)")})


def render_cs_flow_page(db_flow):
    """장비제작 Flow 화면을 그려주는 함수"""
    df_flow, sha_flow = db_flow.load()
    st.markdown("<div class='main-title'>⚙️ CS 작업 체크 시트 (대항목 관리)</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.expander("➕ 새 프로젝트(호기) 시작하기"):
            with st.form("new_proj_form", clear_on_submit=True):
                new_proj = st.text_input("새 프로젝트명 (예: SLH1 #6호기)")
                if st.form_submit_button("템플릿으로 생성") and new_proj and new_proj not in project_list:
                    new_df = pd.DataFrame(CS_TEMPLATE)
                    new_df["프로젝트명"] = new_proj
                    new_df["업데이트일"] = ""
                    new_df['group_id'] = (new_df['대항목'] != new_df['대항목'].shift()).cumsum()
                    new_df["순서"] = new_df.groupby('group_id').cumcount() + 1
                    db_flow.save(pd.concat([df_flow, new_df.drop(columns=['group_id'])], ignore_index=True), sha_flow, f"Create: {new_proj}")
                    st.rerun()

    if project_list:
        with col_b:
            with st.expander("📁 현재 프로젝트에 새 대항목 추가"):
                with st.form("new_cat_form", clear_on_submit=True):
                    new_cat_name = st.text_input("추가할 그룹명 (예: Packing, 출하검수)")
                    if st.form_submit_button("그룹 생성") and new_cat_name:
                        new_cat_row = pd.DataFrame([{
                            "프로젝트명": selected_proj, "대항목": new_cat_name, "순서": 1,
                            "작업내용": "신규 작업 내용을 입력하세요", "상태": "⬜ 대기",
                            "비고": "", "첨부": "", "업데이트일": ""
                        }])
                        db_flow.save(pd.concat([df_flow, new_cat_row], ignore_index=True), sha_flow, f"Add Cat: {new_cat_name}")
                        st.rerun()

        sel_col, empty_col, save_col, del_col = st.columns([6, 2, 1, 1])
        with sel_col: selected_proj = st.selectbox("📌 진행 상황 확인할 프로젝트", project_list)
        with save_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_save = st.button("💾 저장", use_container_width=True)
        with del_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_del = st.button("🗑️ 삭제", use_container_width=True)

        mask = df_flow["프로젝트명"] == selected_proj
        proj_df = df_flow[mask].copy()
        
        st.markdown("<div class='info-box'>💡 <b>편집 가이드:</b> <br>1. <b>[작업내용]</b>을 더블클릭해 직접 수정할 수 있습니다.<br>2. 작업 후 우측 상단의 <b>'💾 저장'</b> 아이콘을 누르면, <b>실제로 상태나 내용을 수정한 항목</b>에만 이름이 기록됩니다. (대기상태는 자동 빈칸 처리)</div>", unsafe_allow_html=True)

        status_options = ["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"]
        custom_column_config = {
            "프로젝트명": None, 
            "대항목": None,    
            "순서": st.column_config.NumberColumn("No", disabled=True, width="small"),
            "작업내용": st.column_config.TextColumn("📝 세부 작업 내용", width="large"), 
            "상태": st.column_config.SelectboxColumn("상태", options=status_options, width="small", required=True), 
            "비고": st.column_config.TextColumn("⚠️ 비고 / 보류사유", width="large"),
            "첨부": st.column_config.TextColumn("📎 첨부(파일명)", width="small"),
            "업데이트일": st.column_config.TextColumn("수정자 & 수정일", disabled=True, width="medium") 
        }

        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        groups = proj_df.groupby('group_id')
        edited_dfs = []

        # 현재 로그인한 유저의 날짜와 이름 도장
        current_user_stamp = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"

        for group_id, group_df in groups:
            cat = group_df['대항목'].iloc[0]
            display_df = group_df.drop(columns=['group_id']).reset_index(drop=True)
            
            with st.expander(f"📍 대항목: {cat} 작업 리스트", expanded=False):
                edited_cat_df = st.data_editor(
                    display_df,
                    use_container_width=False, 
                    hide_index=True, num_rows="dynamic",
                    key=f"editor_{selected_proj}_{group_id}",
                    column_config=custom_column_config
                )
                
                # ★ 스마트 추적 업데이트 로직 ★
                for idx, new_row in edited_cat_df.iterrows():
                    # 1. '대기' 상태면 무조건 이름 지우기 (공백 처리)
                    if new_row['상태'] == "⬜ 대기":
                        edited_cat_df.at[idx, '업데이트일'] = ""
                    else:
                        # 2. 예전 데이터(display_df)와 100% 똑같은 항목이 있는지 검사 (건드렸는지 안건드렸는지 파악)
                        match = display_df[
                            (display_df['작업내용'] == new_row['작업내용']) &
                            (display_df['상태'] == new_row['상태']) &
                            (display_df['비고'] == new_row['비고']) &
                            (display_df['첨부'] == new_row['첨부'])
                        ]
                        
                        if match.empty:
                            # 똑같은 게 없다 = 방금 내가 내용을 수정했다! -> 현재 접속자 이름 쾅!
                            edited_cat_df.at[idx, '업데이트일'] = current_user_stamp
                        else:
                            # 예전이랑 똑같다 = 난 안 건드렸다! -> 예전에 찍혀있던 남의 이름 그대로 복원
                            edited_cat_df.at[idx, '업데이트일'] = match.iloc[0]['업데이트일']
                
                edited_cat_df["대항목"] = cat
                edited_cat_df["프로젝트명"] = selected_proj
                edited_dfs.append(edited_cat_df)

        # 저장 로직
        if btn_save:
            updated_proj_df = pd.concat(edited_dfs, ignore_index=True)
            if not updated_proj_df.empty:
                updated_proj_df['group_id'] = (updated_proj_df['대항목'] != updated_proj_df['대항목'].shift()).cumsum()
                updated_proj_df["순서"] = updated_proj_df.groupby('group_id').cumcount() + 1
                updated_proj_df = updated_proj_df.drop(columns=['group_id'])
            
            df_flow = pd.concat([df_flow[~mask], updated_proj_df], ignore_index=True)
            db_flow.save(df_flow, sha_flow, f"Update: {selected_proj}")
            st.success("✅ 변경사항이 안전하게 저장되었습니다.")
            st.rerun()

        # 삭제 로직
        if btn_del:
            db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
            st.warning("🗑️ 프로젝트가 삭제되었습니다.")
            st.rerun()
    else:
        st.info("진행 중인 프로젝트가 없습니다.")


# ==========================================
# 4. 메인 실행 (Main App)
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

    if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user_name': ""})
    
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            name = st.text_input("성함을 입력하세요")
            if st.form_submit_button("입장하기") and name:
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        st.sidebar.markdown(f"👤 {st.session_state['user_name']} 님")
        if st.sidebar.button("로그아웃"): 
            st.session_state['logged_in'] = False
            st.rerun()
        
        st.sidebar.divider()
        page_menu = st.sidebar.radio("📌 메뉴 이동", ["📝 팀 업무일지", "⚙️ 장비제작 Flow"])
        
        if page_menu == "📝 팀 업무일지": render_work_log_page(db_log)
        elif page_menu == "⚙️ 장비제작 Flow": render_cs_flow_page(db_flow)

if __name__ == "__main__":
    main()
