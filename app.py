import streamlit as st
import pandas as pd
from github import Github
import io
import re
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 환경 설정 및 전체 디자인 (CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        .main-title { font-size: 1.5rem !important; font-weight: bold; padding-bottom: 10px !important; }
        .info-box { background-color: #f8f9fa; padding: 12px; border-radius: 4px; border-left: 5px solid #4CAF50; margin-bottom: 15px; color: #333; font-size: 13px; }
        
        /* 장비 가동 데이터 표 테두리 아주 진하게 */
        .final-report-table {
            width: 100%; border-collapse: collapse; border: 2px solid #000000 !important;
            font-size: 12px; color: #000000; background-color: #ffffff;
        }
        .final-report-table th, .final-report-table td {
            border: 1px solid #000000 !important; padding: 6px 8px; text-align: center;
        }
        .final-report-table th { background-color: #d9e1f2 !important; font-weight: bold; }
        .t-left { text-align: left !important; }
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
# 2. 데이터 관리 코어
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
# 3. 메뉴 1: 팀 업무일지 (사이드바 통제 완벽 적용)
# ==========================================
def render_work_log_page(db_log):
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

    # 이 메뉴에서만 작동하는 사이드바
    st.sidebar.markdown("---")
    mode = st.sidebar.selectbox("📋 일지 작업", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
    
    if mode == "➕ 작성":
        with st.sidebar.form("add_log", clear_on_submit=True):
            d = st.date_input("날짜", datetime.today())
            e = st.selectbox("장비", EQUIPMENT_OPTIONS)
            c = st.text_area("업무 내용", height=300)
            n = st.text_input("비고")
            if st.form_submit_button("저장하기"):
                new_row = pd.DataFrame([{"날짜": str(d), "장비": e, "작성자": st.session_state['user_name'], "업무내용": c, "비고": n}])
                db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d}")
                st.rerun()

    elif mode == "✏️ 수정" and not df_log.empty:
        idx = st.sidebar.selectbox("수정 대상", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:15]}...")
        with st.sidebar.form("edit_log"):
            e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[idx, '날짜']))
            e_content = st.text_area("내용 수정", value=df_log.loc[idx, '업무내용'], height=300)
            if st.form_submit_button("수정 완료"):
                df_log.loc[idx, ['날짜', '업무내용']] = [str(e_date), e_content]
                db_log.save(df_log, sha_log, "Edit Log")
                st.rerun()

    elif mode == "❌ 삭제" and not df_log.empty:
        idx = st.sidebar.selectbox("삭제 대상 선택", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:10]}")
        st.sidebar.warning(f"내용: {df_log.loc[idx, '업무내용'][:50]}...")
        if st.sidebar.button("🗑️ 최종 삭제 (복구 불가)"):
            db_log.save(df_log.drop(idx), sha_log, "Delete Log")
            st.rerun()

    col_title, col_excel = st.columns([8.5, 1.5])
    with col_title:
        st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    with col_excel:
        csv_data = df_log.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(label="📥 엑셀 다운로드", data=csv_data, file_name=f"work_log_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    search = st.text_input("🔍 검색어 (장비, 내용 등)", placeholder="검색어를 입력하세요...")
    disp = df_log.copy()
    if search: disp = disp[disp.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(disp, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("업무내용", width="large")})

# ==========================================
# 4. 메뉴 2: CS 작업체크시트
# ==========================================
def render_cs_flow_page(db_flow):
    df_flow, sha_flow = db_flow.load()
    
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
                new_proj = st.text_input("새 프로젝트명 (예: 4010H #2호기)")
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
            selected_proj = st.selectbox("📌 진행 상황 확인할 프로젝트", project_list, index=default_idx, format_func=lambda x: progress_dict.get(x, x))
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
            st.error(f"🚨 [{selected_proj}] 프로젝트를 영구 삭제하시겠습니까? (복구 불가)")
            if st.button("⚠️ 완전히 삭제합니다", type="primary"):
                db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
                st.session_state['delete_target_proj'] = None
                st.session_state['current_proj'] = project_list[0] if len(project_list) > 1 else ""
                st.rerun()
            if st.button("❌ 취소"):
                st.session_state['delete_target_proj'] = None
                st.rerun()
            st.stop() 

        total_tasks = len(proj_df)
        comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
        pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
        
        st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#4CAF50;'>⚡ 셋업 전체 진행도 ({comp_tasks} / {total_tasks} 완료)</div>", unsafe_allow_html=True)
        st.progress(pct_float, text=f"전체 {int(pct_float * 100)}% 완료됨")

        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        groups = proj_df.groupby('group_id', sort=False) 
        
        edited_dfs = []
        current_user_stamp = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"

        for group_id, group_df in groups:
            cat = group_df['대항목'].iloc[0]
            display_df = group_df.drop(columns=['group_id']).reset_index(drop=True)
            
            current_statuses = display_df['상태'].tolist()
            if '🚨 보류' in current_statuses: tab_title = f"🔴 [보류발생] 대항목: {cat}"
            elif current_statuses and all(s == '✅ 완료' for s in current_statuses): tab_title = f"🟢 [완료] 대항목: {cat}"
            elif '⏳ 작업중' in current_statuses or '✅ 완료' in current_statuses: tab_title = f"🟡 [진행중] 대항목: {cat}"
            else: tab_title = f"📍 [대기] 대항목: {cat}"
            
            with st.expander(tab_title, expanded=False):
                styled_df = display_df.style.apply(get_row_color, axis=1)
                edited_cat_df = st.data_editor(
                    styled_df, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"editor_{selected_proj}_{group_id}",
                    column_config={"순서": st.column_config.NumberColumn("No", width="small"), "작업내용": st.column_config.TextColumn("세부 작업 내용", width="large"), "상태": st.column_config.SelectboxColumn("상태", options=["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"], width="small")}
                )
                
                for idx, new_row in edited_cat_df.iterrows():
                    if new_row['상태'] == "⬜ 대기": edited_cat_df.at[idx, '업데이트일'] = ""
                    else:
                        match = display_df[(display_df['작업내용'] == new_row['작업내용']) & (display_df['상태'] == new_row['상태']) & (display_df['비고'] == new_row['비고'])]
                        if match.empty: edited_cat_df.at[idx, '업데이트일'] = current_user_stamp
                        else: edited_cat_df.at[idx, '업데이트일'] = match.iloc[0]['업데이트일']
                
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
# 5. 메뉴 3: 장비 가동 데이터 (장비/호기명 조합 파일명 적용)
# ==========================================
def render_equipment_data_page():
    st.markdown("<div class='main-title'>📊 장비 가동 데이터 정밀 분석</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: equipment = st.selectbox("장비 선택", EQUIPMENT_OPTIONS, key="eq_data_equip")
    with col2: unit = st.selectbox("호기 선택", ["1호기", "2호기", "3호기", "4호기", "5호기"], key="eq_data_unit")
    with col3: month_str = st.selectbox("조회할 월 선택", [f"{i}월" for i in range(1, 13)], key="eq_data_month")

    # ★ 핵심 2: 선택한 장비, 호기, 월을 조합하여 엑셀 파일명을 똑똑하게 만들어냅니다.
    month_dict = {"1월": "January", "2월": "February", "3월": "March", "4월": "April", "5월": "May", "6월": "June", 
                  "7월": "July", "8월": "August", "9월": "September", "10월": "October", "11월": "November", "12월": "December"}
    eng_month = month_dict.get(month_str, "January")

    # 기존에 테스트하시던 SLH1 1호기는 기존 파일명 규칙을 유지하고, 나머지는 새로운 규칙을 따릅니다.
    if equipment == "SLH1" and unit == "1호기" and month_str in ["1월", "2월", "3월"]:
        target_file = f"SLH1 - {eng_month} 2026.xlsx"
    else:
        # 새로운 규칙 예시: "4010H_2호기 - April 2026.xlsx"
        target_file = f"{equipment}_{unit} - {eng_month} 2026.xlsx"

    st.info(f"📂 현재 조회 요청 파일: **{target_file}** (해당 파일이 깃허브에 업로드 되어 있어야 데이터가 나옵니다)")

    try:
        xls = pd.read_excel(target_file, sheet_name=None, header=None, engine='openpyxl')
        df_raw = None
        for name, data in xls.items():
            if data.astype(str).apply(lambda r: r.str.contains('Unit|Output', case=False).any(), axis=1).any():
                df_raw = data; break
        
        if df_raw is None:
            st.error("⚠️ 데이터를 찾을 수 없습니다. (시트 내 'Total Unit' 글자가 있는지 확인하세요)"); return

        def get_sum_row(keywords):
            for _, row in df_raw.iterrows():
                row_str = "".join(row.astype(str)).lower().replace(" ", "").replace("#", "").replace("_", "")
                if any(k in row_str for k in keywords) and not any(x in row_str for x in ['%', '발생률']):
                    vals = row.tolist()
                    for i, v in enumerate(vals):
                        v_s = str(v).replace('.','').replace(',','').strip()
                        if v_s.isdigit() or v_s in ['비가동', '미가동']: return (vals[i:i+31]+[0]*31)[:31]
            return [0]*31

        month_num = month_str.replace("월", "")
        units = get_sum_row(['totalunit', 'output'])
        jams = get_sum_row(['jamcount', 'jam'])
        ppjs = get_sum_row(['ppj'])

        chart_df = pd.DataFrame({'날짜': [f"{month_num}/{i}" for i in range(1, 32)], 'Unit': units, 'Jam': jams, 'PPJ': ppjs})
        for c in ['Unit', 'Jam', 'PPJ']:
            chart_df[c] = pd.to_numeric(chart_df[c].astype(str).str.replace(',', '').replace(['nan','비가동','미가동','None',''], '0'), errors='coerce').fillna(0)

        chart_df['Cum_Unit'] = chart_df['Unit'].cumsum()
        chart_df['Cum_Jam'] = chart_df['Jam'].cumsum()
        chart_df['Cum_PPJ'] = chart_df.apply(lambda row: round(row['Cum_Unit'] / row['Cum_Jam'], 1) if row['Cum_Jam'] > 0 else 0, axis=1)

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                            subplot_titles=("투입량(Unit) 및 에러(Jam) 건수", "생산 효율(PPJ) 추이"),
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
        
        fig.add_trace(go.Bar(x=chart_df['날짜'], y=chart_df['Unit'], name='투입(Unit)', marker_color='#5B9BD5'), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['Jam'], name='에러(Jam)', mode='lines+markers', line=dict(color='#ED7D31', width=2)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Bar(x=chart_df['날짜'], y=chart_df['PPJ'], name='일별 PPJ', marker_color='#A9D18E', opacity=0.8), row=2, col=1)
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['Cum_PPJ'], name='월 누적 PPJ (실선)', mode='lines+markers', line=dict(color='#FF0000', width=4)), row=2, col=1)
        
        fig.update_layout(height=650, margin=dict(l=50, r=50, t=50, b=50), hovermode="x unified", showlegend=True)
        fig.update_yaxes(title_text="투입량 (EA)", secondary_y=False, row=1, col=1)
        fig.update_yaxes(title_text="Jam (건)", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="PPJ", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(f"📋 {month_str} 에러 상세 리스트")
        h_idx = -1
        for i, row in df_raw.iterrows():
            row_str = "".join(row.astype(str)).lower()
            if 'error code' in row_str or 'errorcode' in row_str or '에러코드' in row_str:
                h_idx = i; break

        if h_idx != -1:
            m = {'D': -1, 'C': -1, 'M': -1, 'A': -1, 'T': -1, 'L': -1, 'P': -1}
            super_headers = []
            for col_idx in range(len(df_raw.columns)):
                col_strs = []
                for offset in [-1, 0, 1]:
                    if 0 <= h_idx + offset < len(df_raw):
                        val = str(df_raw.iloc[h_idx + offset, col_idx]).lower().replace(' ', '').replace('\n', '')
                        if val not in ['nan', 'none', 'null', '']: col_strs.append(val)
                super_headers.append("".join(col_strs))
            
            for i, v_str in enumerate(super_headers):
                if m['D'] == -1 and ('date' in v_str or '일자' in v_str): m['D'] = i
                elif m['C'] == -1 and ('errorcode' in v_str or '에러코드' in v_str): m['C'] = i
                elif m['M'] == -1 and ('massage' in v_str or 'message' in v_str or '에러내용' in v_str): m['M'] = i
                elif m['A'] == -1 and ('finding' in v_str or 'action' in v_str or '조치' in v_str): m['A'] = i
                elif m['T'] == -1 and ('time' in v_str or '시간' in v_str): m['T'] = i
                elif m['L'] == -1 and ('point' in v_str or '위치' in v_str): m['L'] = i
                elif m['P'] == -1 and ('ppj' in v_str or '효율' in v_str): m['P'] = i

            if m['P'] == -1 and m['M'] != -1: m['P'] = m['M'] - 1

            data_slice = df_raw.iloc[h_idx + 1:].copy()
            cleaned_list = []
            
            def is_meaningful(val):
                if pd.isna(val): return False
                cleaned = re.sub(r'[^a-zA-Z0-9가-힣]', '', str(val))
                return len(cleaned) > 0

            def get_val(r, idx): return r.iloc[idx] if idx != -1 and idx < len(r) else None

            for _, r in data_slice.iterrows():
                raw_c = get_val(r, m['C'])
                raw_m = get_val(r, m['M'])
                has_code = is_meaningful(raw_c)
                has_msg = is_meaningful(raw_m)
                
                if not has_code and not has_msg: continue
                
                code_orig = str(raw_c).strip() if has_code else ""
                if code_orig.endswith('.0'): code_orig = code_orig[:-2]
                msg_orig = str(raw_m).strip() if has_msg else ""
                if msg_orig.lower() in ['nan', 'none']: msg_orig = ""

                raw_d = get_val(r, m['D'])
                dt = None
                if is_meaningful(raw_d):
                    if str(raw_d).replace('.','').isdigit(): dt = pd.to_datetime(float(raw_d), unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
                    else: dt = str(raw_d).split(' ')[0]

                raw_p = get_val(r, m['P'])
                ppj_val = None
                if is_meaningful(raw_p) and str(raw_p).lower() not in ['nan', 'none']: ppj_val = str(raw_p).split('.')[0]

                raw_t = get_val(r, m['T'])
                t_val = ""
                if is_meaningful(raw_t) and str(raw_t).lower() not in ['nan', 'none']: t_val = str(raw_t).split('.')[0] if ':' in raw_t else raw_t
                
                raw_a = get_val(r, m['A'])
                a_val = str(raw_a).strip() if is_meaningful(raw_a) and str(raw_a).lower() not in ['nan', 'none'] else ""

                raw_l = get_val(r, m['L'])
                l_val = str(raw_l).strip() if is_meaningful(raw_l) and str(raw_l).lower() not in ['nan', 'none'] else ""

                cleaned_list.append({"Date": dt, "Code": code_orig, "PPJ": ppj_val, "Msg": msg_orig, "Act": a_val, "Time": t_val, "Loc": l_val})

            if cleaned_list:
                final_df = pd.DataFrame(cleaned_list)
                final_df['Date'] = final_df['Date'].replace(['', 'nan', 'None'], pd.NA).ffill()
                final_df['PPJ'] = final_df['PPJ'].replace(['', 'nan', 'None'], pd.NA).ffill().fillna("0")
                
                rows_html = ""
                for _, row in final_df.iterrows():
                    date_td = f"{row['Date']}" if not pd.isna(row['Date']) else ""
                    rows_html += f"<tr><td style='width:75px;'>{date_td}</td><td style='width:60px;'>{row['Code']}</td><td style='width:60px;'>{row['PPJ']}</td><td class='t-left'>{row['Msg']}</td><td class='t-left'>{row['Act']}</td><td style='width:65px;'>{row['Time']}</td><td style='width:90px;'>{row['Loc']}</td></tr>"
                
                st.markdown(f"<table class='final-report-table'><thead><tr><th style='width:75px;'>날짜</th><th style='width:60px;'>코드</th><th style='width:60px;'>PPJ</th><th>에러내용</th><th>조치내용</th><th style='width:65px;'>시간</th><th style='width:90px;'>위치</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
            else: st.info("상세 데이터가 없습니다.")
        else: st.info("데이터 헤더를 찾을 수 없습니다.")

    except FileNotFoundError: st.error(f"⚠️ 깃허브 저장소에 **{target_file}** 파일이 없습니다. 장비/호기/월에 맞는 파일을 업로드해주세요.")
    except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")

# ==========================================
# 6. 메인 실행 (로그인 및 ★ 페이지 네비게이션)
# ==========================================
def main():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 깃허브 연결 설정 오류: {e}")
        return

    if 'logged_in' not in st.session_state: 
        st.session_state.update({'logged_in': False, 'user_name': ""})
    
    if not st.session_state['logged_in']:
        with st.form("login_form"):
            name = st.text_input("성함을 입력하세요")
            if st.form_submit_button("입장하기") and name:
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        # 사이드바 상단
        st.sidebar.markdown(f"👤 **{st.session_state['user_name']}** 님 환영합니다.")
        if st.sidebar.button("🚪 로그아웃", use_container_width=True): 
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.sidebar.markdown("---")
        
        # ★ 핵심 1: 화면 위쪽 탭(Tabs)을 사이드바 메뉴(Radio)로 완전히 이동시켰습니다!
        menu = st.sidebar.radio("📂 대시보드 메뉴 이동", ["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터"])
        
        if menu == "📝 업무일지":
            render_work_log_page(db_log)
        elif menu == "✅ CS 작업체크시트":
            render_cs_flow_page(db_flow)
        elif menu == "📊 장비가동데이터":
            render_equipment_data_page()

if __name__ == "__main__":
    main()
