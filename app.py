import streamlit as st
import pandas as pd
from github import Github
import io
import re
import calendar
from datetime import datetime, date
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import openpyxl

# ==========================================
# 1. 환경 설정 및 전체 디자인 (CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { padding-top: 3.5rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        .main-title { font-size: 1.5rem !important; font-weight: bold; padding-bottom: 10px !important; margin-top: -10px; }
        .info-box { background-color: #f8f9fa; padding: 12px; border-radius: 4px; border-left: 5px solid #4CAF50; margin-bottom: 15px; color: #333; font-size: 13px; }
        
        .final-report-table {
            width: 100%; border-collapse: collapse; border: 2px solid #000000 !important;
            font-size: 12px; color: #000000; background-color: #ffffff;
        }
        .final-report-table th, .final-report-table td {
            border: 1px solid #000000 !important; padding: 6px 8px; text-align: center;
        }
        .final-report-table th { background-color: #d9e1f2 !important; font-weight: bold; }
        .t-left { text-align: left !important; }
        
        div[data-testid="stSidebar"] button { width: 100% !important; font-weight: bold; }
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
# 3. 화면 UI - 1페이지: 팀 업무일지 
# ==========================================
def render_work_log_page(db_log):
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 일지 작성/수정/삭제")
    mode = st.sidebar.selectbox("기능 선택", ["➕ 작성", "✏️ 수정", "❌ 삭제"])
    
    if mode == "➕ 작성":
        with st.sidebar.form("add_log", clear_on_submit=True):
            d = st.date_input("날짜", datetime.today())
            e = st.selectbox("장비", EQUIPMENT_OPTIONS)
            c = st.text_area("업무 내용", height=300)
            n = st.text_input("비고")
            a = st.text_input("첨부 (FTP 경로 등)")
            if st.form_submit_button("저장하기"):
                new_row = pd.DataFrame([{"날짜": str(d), "장비": e, "작성자": st.session_state['user_name'], "업무내용": c, "비고": n, "첨부": a}])
                db_log.save(pd.concat([df_log, new_row], ignore_index=True), sha_log, f"Add Log: {d}")
                st.rerun()

    elif mode == "✏️ 수정" and not df_log.empty:
        idx = st.sidebar.selectbox("수정 대상", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:15]}...")
        with st.sidebar.form("edit_log"):
            e_date = st.date_input("날짜 수정", pd.to_datetime(df_log.loc[idx, '날짜']))
            e_content = st.text_area("내용 수정", value=df_log.loc[idx, '업무내용'], height=300)
            
            val_note = df_log.loc[idx, '비고'] if '비고' in df_log.columns else ""
            val_note = "" if pd.isna(val_note) else str(val_note)
            e_note = st.text_input("비고 수정", value=val_note)
            
            val_attach = df_log.loc[idx, '첨부'] if '첨부' in df_log.columns else ""
            val_attach = "" if pd.isna(val_attach) else str(val_attach)
            e_attach = st.text_input("첨부 수정", value=val_attach)
            
            if st.form_submit_button("수정 완료"):
                df_log.loc[idx, ['날짜', '업무내용', '비고', '첨부']] = [str(e_date), e_content, e_note, e_attach]
                db_log.save(df_log, sha_log, "Edit Log")
                st.rerun()

    elif mode == "❌ 삭제" and not df_log.empty:
        idx = st.sidebar.selectbox("삭제 대상 선택", df_log.index, format_func=lambda x: f"{df_log.loc[x, '날짜']} | {df_log.loc[x, '업무내용'][:10]}")
        st.sidebar.warning(f"내용: {df_log.loc[idx, '업무내용'][:50]}...")
        if st.sidebar.button("🗑️ 최종 삭제 (복구 불가)", type="primary"):
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
    
    st.dataframe(
        disp, 
        use_container_width=True, 
        hide_index=True, 
        column_config={
            "업무내용": st.column_config.TextColumn("업무내용", width="large"),
            "비고": st.column_config.TextColumn("비고", width="small"),
            "첨부": st.column_config.TextColumn("첨부", width="small")
        }
    )

# ==========================================
# 4. 화면 UI - 2페이지: CS 작업체크시트
# ==========================================
def render_cs_flow_page(db_flow):
    df_flow, sha_flow = db_flow.load()
    st.markdown("<div class='main-title'>✅ CS 작업 체크 시트</div>", unsafe_allow_html=True)
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
                source_proj = st.selectbox("어떤 형식을 복사할까요?", source_options, format_func=lambda x: progress_dict.get(x, x))
                if st.form_submit_button("프로젝트 생성하기") and new_proj and new_proj not in project_list:
                    if source_proj == "기본 템플릿(초기화 상태)": new_df = pd.DataFrame(CS_TEMPLATE)
                    else:
                        new_df = df_flow[df_flow["프로젝트명"] == source_proj].copy()
                        new_df[["상태", "비고", "첨부", "업데이트일"]] = ["⬜ 대기", "", "", ""]
                    new_df["프로젝트명"] = new_proj
                    db_flow.save(pd.concat([df_flow, new_df], ignore_index=True), sha_flow, f"Create: {new_proj}")
                    st.session_state['current_proj'] = new_proj
                    st.rerun()

    if project_list:
        sel_col, empty_col, save_col, del_col = st.columns([6, 2, 1, 1])
        default_idx = project_list.index(st.session_state['current_proj']) if project_list else 0
        with sel_col: 
            selected_proj = st.selectbox("📌 프로젝트 선택", project_list, index=default_idx, format_func=lambda x: progress_dict.get(x, x))
            st.session_state['current_proj'] = selected_proj 
        with save_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            btn_save = st.button("💾 변경 저장", use_container_width=True)
        with del_col: 
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🗑️ 삭제", use_container_width=True):
                st.session_state['delete_target_proj'] = selected_proj
                st.rerun()

        mask = df_flow["프로젝트명"] == selected_proj
        proj_df = df_flow[mask].copy()

        if st.session_state.get('delete_target_proj') == selected_proj:
            st.error(f"🚨 [{selected_proj}] 프로젝트를 영구 삭제하시겠습니까?")
            if st.button("⚠️ 삭제 확정", type="primary"):
                db_flow.save(df_flow[~mask], sha_flow, f"Delete: {selected_proj}")
                st.session_state['delete_target_proj'] = None
                st.session_state['current_proj'] = project_list[0] if len(project_list) > 1 else ""
                st.rerun()
            if st.button("❌ 취소"): st.session_state['delete_target_proj'] = None; st.rerun()
            st.stop() 

        cats = proj_df['대항목'].unique().tolist()
        with st.expander("⚙️ 프로젝트 대항목 관리 (추가/수정/삭제/순서변경)"):
            c1, c2, c3, c4 = st.tabs(["➕ 대항목 추가", "✏️ 이름 수정", "❌ 대항목 삭제", "↕️ 순서 변경"])
            
            with c1:
                with st.form("add_cat_form", clear_on_submit=True):
                    new_c = st.text_input("새 대항목 이름")
                    if st.form_submit_button("추가하기"):
                        if new_c and new_c not in cats:
                            new_row = pd.DataFrame([{"프로젝트명": selected_proj, "대항목": new_c, "순서": 1, "작업내용": "새 작업 내용 입력", "상태": "⬜ 대기", "비고": "", "첨부": "", "업데이트일": ""}])
                            db_flow.save(pd.concat([df_flow, new_row], ignore_index=True), sha_flow, f"Add Cat: {new_c}")
                            st.success(f"'{new_c}' 항목이 추가되었습니다.")
                            st.rerun()

            with c2:
                with st.form("edit_cat_form", clear_on_submit=True):
                    target_c = st.selectbox("수정할 대항목 선택", cats)
                    rename_c = st.text_input("새로운 이름 입력")
                    if st.form_submit_button("이름 변경"):
                        if rename_c and rename_c not in cats:
                            df_flow.loc[(df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == target_c), "대항목"] = rename_c
                            db_flow.save(df_flow, sha_flow, f"Rename Cat: {target_c}")
                            st.success("이름이 변경되었습니다.")
                            st.rerun()

            with c3:
                with st.form("del_cat_form"):
                    del_c = st.selectbox("삭제할 대항목 선택", cats)
                    st.warning("⚠️ 해당 대항목과 안에 포함된 모든 세부 작업이 영구 삭제됩니다.")
                    if st.form_submit_button("삭제 실행"):
                        df_flow = df_flow[~((df_flow["프로젝트명"] == selected_proj) & (df_flow["대항목"] == del_c))]
                        db_flow.save(df_flow, sha_flow, f"Delete Cat: {del_c}")
                        st.success("삭제되었습니다.")
                        st.rerun()

            with c4:
                st.write("표 안의 **'새 순서'** 숫자를 클릭하여 순서를 변경하고 적용 버튼을 누르세요.")
                order_df = pd.DataFrame({"대항목": cats, "새 순서": range(1, len(cats)+1)})
                edited_order = st.data_editor(order_df, hide_index=True, use_container_width=True)
                if st.button("변경된 순서 적용하기"):
                    edited_order = edited_order.sort_values("새 순서")
                    ordered_cats = edited_order["대항목"].tolist()
                    proj_df['__cat_order__'] = pd.Categorical(proj_df['대항목'], categories=ordered_cats, ordered=True)
                    sorted_proj_df = proj_df.sort_values(['__cat_order__', '순서']).drop(columns=['__cat_order__'])
                    
                    new_df_flow = df_flow[df_flow["프로젝트명"] != selected_proj]
                    new_df_flow = pd.concat([new_df_flow, sorted_proj_df], ignore_index=True)
                    db_flow.save(new_df_flow, sha_flow, "Reorder Cats")
                    st.success("순서가 적용되었습니다.")
                    st.rerun()

        total_tasks = len(proj_df); comp_tasks = len(proj_df[proj_df["상태"] == "✅ 완료"])
        pct_float = (comp_tasks / total_tasks) if total_tasks > 0 else 0.0
        st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#4CAF50;'>⚡ 진행도 ({comp_tasks} / {total_tasks})</div>", unsafe_allow_html=True)
        st.progress(pct_float, text=f"{int(pct_float * 100)}% 완료")

        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        groups = proj_df.groupby('group_id', sort=False) 
        edited_dfs = []; current_user_stamp = f"{st.session_state['user_name']} ({datetime.today().strftime('%y-%m-%d')})"

        for group_id, group_df in groups:
            cat = group_df['대항목'].iloc[0]
            display_df = group_df.drop(columns=['group_id']).reset_index(drop=True)
            curr_stats = display_df['상태'].tolist()
            if '🚨 보류' in curr_stats: tab_title = f"🔴 [보류] {cat}"
            elif curr_stats and all(s == '✅ 완료' for s in curr_stats): tab_title = f"🟢 [완료] {cat}"
            elif any(s in ['⏳ 작업중', '✅ 완료'] for s in curr_stats): tab_title = f"🟡 [진행] {cat}"
            else: tab_title = f"📍 [대기] {cat}"
            
            with st.expander(tab_title, expanded=False):
                styled_df = display_df.style.apply(get_row_color, axis=1)
                edited_cat_df = st.data_editor(
                    styled_df, use_container_width=True, hide_index=True, num_rows="dynamic", key=f"editor_{selected_proj}_{group_id}",
                    column_config={
                        "순서": st.column_config.NumberColumn("No", width="small"), 
                        "작업내용": st.column_config.TextColumn("세부 작업 내용", width="large"), 
                        "상태": st.column_config.SelectboxColumn("상태", options=["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"], width="small"),
                        "비고": st.column_config.TextColumn("비고", width="small"),
                        "첨부": st.column_config.TextColumn("첨부", width="small")
                    }
                )
                for idx, new_row in edited_cat_df.iterrows():
                    if new_row['상태'] == "⬜ 대기": edited_cat_df.at[idx, '업데이트일'] = ""
                    else:
                        match = display_df[(display_df['작업내용'] == new_row['작업내용']) & (display_df['상태'] == new_row['상태']) & (display_df['비고'] == new_row['비고'])]
                        if match.empty: edited_cat_df.at[idx, '업데이트일'] = current_user_stamp
                        else: edited_cat_df.at[idx, '업데이트일'] = match.iloc[0]['업데이트일']
                edited_cat_df["대항목"] = cat; edited_cat_df["프로젝트명"] = selected_proj; edited_cat_df["org_group_id"] = group_id 
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
            db_flow.save(maintain_project_order(new_df_flow, original_projects), sha_flow, f"Update: {selected_proj}")
            st.success("✅ 저장되었습니다!"); st.rerun()
    else: st.info("프로젝트가 없습니다.")

# ==========================================
# 5. 화면 UI - 3페이지: 장비 가동 데이터 
# ==========================================
def render_equipment_data_page(repo):
    import re
    from plotly.subplots import make_subplots
    import pandas as pd

    st.markdown("""
        <style>
            .final-report-table {
                width: 100%; border-collapse: collapse; border: 2px solid #000000 !important;
                font-size: 12px; color: #000000; background-color: #ffffff;
            }
            .final-report-table th, .final-report-table td {
                border: 1px solid #000000 !important; padding: 6px 8px; text-align: center !important;
            }
            .final-report-table th { background-color: #d9e1f2 !important; font-weight: bold; }
            .t-left { text-align: left !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>📊 장비 가동 데이터 정밀 분석</div>", unsafe_allow_html=True)
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
            if data.astype(str).apply(lambda r: r.str.contains('Unit|Output', case=False).any(), axis=1).any():
                df_raw = data; break
        
        if df_raw is None:
            st.error("⚠️ 가동 데이터를 찾을 수 없습니다."); return

        def get_sum_row(keywords):
            for _, row in df_raw.iterrows():
                row_str = "".join(row.astype(str)).lower().replace(" ", "").replace("#", "").replace("_", "")
                if any(k in row_str for k in keywords) and not any(x in row_str for x in ['%', '발생률']):
                    vals = row.tolist()
                    for i, v in enumerate(vals):
                        v_s = str(v).replace('.','').replace(',','').strip()
                        if v_s.isdigit() or v_s in ['비가동', '미가동']: return (vals[i:i+31]+[0]*31)[:31]
            return [0]*31

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
            if 'error code' in row_str or 'errorcode' in row_str:
                h_idx = i; h_row = row.tolist(); break

        if h_idx != -1:
            m = {'D': None, 'C': None, 'M': None, 'A': None, 'T': None, 'L': None, 'P': None}
            for i, v in enumerate(h_row):
                v_str = str(v).lower().replace(' ', '').replace('\n', '')
                if m['D'] is None and 'date' in v_str: m['D'] = i
                elif m['C'] is None and 'errorcode' in v_str: m['C'] = i
                elif m['M'] is None and ('massage' in v_str or 'message' in v_str): m['M'] = i
                elif m['A'] is None and ('finding' in v_str or 'action' in v_str): m['A'] = i
                elif m['T'] is None and 'time' in v_str: m['T'] = i
                elif m['L'] is None and 'point' in v_str: m['L'] = i
                elif m['P'] is None and 'ppj' in v_str: m['P'] = i

            data_slice = df_raw.iloc[h_idx + 1:].copy()
            cleaned_list = []
            
            def is_meaningful(val):
                if pd.isna(val): return False
                cleaned = re.sub(r'[^a-zA-Z0-9가-힣]', '', str(val))
                return len(cleaned) > 0

            for _, r in data_slice.iterrows():
                has_code = is_meaningful(r[m['C']]) if m['C'] is not None else False
                has_msg = is_meaningful(r[m['M']]) if m['M'] is not None else False
                
                if not has_code and not has_msg:
                    continue
                
                code_orig = str(r[m['C']]).strip() if m['C'] is not None else ""
                if code_orig.endswith('.0'): code_orig = code_orig[:-2]
                
                msg_orig = str(r[m['M']]).strip() if m['M'] is not None else ""
                if msg_orig.lower() in ['nan', 'none']: msg_orig = ""

                dt = None
                if m['D'] is not None:
                    raw_d = r[m['D']]
                    if is_meaningful(raw_d):
                        if str(raw_d).replace('.','').isdigit():
                            dt = pd.to_datetime(float(raw_d), unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
                        else:
                            dt = str(raw_d).split(' ')[0]

                ppj_val = None
                if m['P'] is not None and m['P'] < len(r):
                    raw_p = str(r[m['P']]).strip()
                    if is_meaningful(raw_p) and raw_p.lower() not in ['nan', 'none']:
                        ppj_val = raw_p.split('.')[0]

                t_val = ""
                if m['T'] is not None and m['T'] < len(r):
                    raw_t = str(r[m['T']]).strip()
                    if is_meaningful(raw_t) and raw_t.lower() not in ['nan', 'none']: 
                        t_val = raw_t.split('.')[0] if ':' in raw_t else raw_t
                
                a_val = ""
                if m['A'] is not None and m['A'] < len(r):
                    raw_a = str(r[m['A']]).strip()
                    if is_meaningful(raw_a) and raw_a.lower() not in ['nan', 'none']: a_val = raw_a

                l_val = ""
                if m['L'] is not None and m['L'] < len(r):
                    raw_l = str(r[m['L']]).strip()
                    if is_meaningful(raw_l) and raw_l.lower() not in ['nan', 'none']: l_val = raw_l

                cleaned_list.append({
                    "Date": dt, "Code": code_orig, "PPJ": ppj_val,
                    "Msg": msg_orig, "Act": a_val, "Time": t_val, "Loc": l_val
                })

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

    except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")

# ==========================================
# 6. 화면 UI - 4페이지: ECN & STN (★ 자동 저장 기능 엑셀 원본 양식 보존형으로 강화)
# ==========================================
def render_ecn_stn_page(repo):
    st.markdown("<div class='main-title'>🛠️ ECN & STN (장비 파트 및 수정사항 관리)</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1: equipment = st.selectbox("장비 선택", EQUIPMENT_OPTIONS, key="ecn_equip")
    with col2: unit = st.selectbox("호기 선택", ["전체"] + [f"{i}호기" for i in range(1, 16)], key="ecn_unit")
    
    target_file = f"data/ECN/ECN_STN_Master({equipment}).xlsx"
    
    st.info(f"💡 **이용 안내:** 깃허브 `data/ECN/` 폴더 안의 **`ECN_STN_Master({equipment}).xlsx`** 파일을 기반으로 목록을 출력합니다.\n\n"
            f"엑셀 파일 내에 **'날짜', '발행부서', '발행자', '장비호기', 'ECN No', '내용', '변경', '특이사항', '조치현황', '첨부'** 열이 존재해야 작동합니다.")

    try:
        file_content = repo.get_contents(target_file)
        raw_bytes = file_content.decoded_content
        excel_data = io.BytesIO(raw_bytes)
        
        # 1. 헤더 없이 다중 시트 가능성을 고려해 읽어옵니다.
        xls_dict = pd.read_excel(excel_data, engine='openpyxl', header=None, sheet_name=None)
        sheet_names = list(xls_dict.keys())
        first_sheet = sheet_names[0]
        df_raw = xls_dict[first_sheet]
        
        h_idx = -1
        for i, row in df_raw.head(20).iterrows():
            row_str = "".join(row.astype(str)).replace(" ", "").lower()
            if '날짜' in row_str and ('발행' in row_str or '장비호기' in row_str or '내용' in row_str or 'as-is' in row_str):
                h_idx = i
                break
        
        if h_idx != -1:
            df = df_raw.iloc[h_idx + 1:].reset_index(drop=True)
            orig_cols = df_raw.iloc[h_idx].tolist()
            # ★ 엑셀 원본의 진짜 행 번호를 추적 (수정을 위해)
            df['Original_Index'] = range(h_idx + 1, len(df_raw))
        else:
            df = df_raw.iloc[1:].reset_index(drop=True)
            orig_cols = df_raw.iloc[0].tolist()
            df['Original_Index'] = range(1, len(df_raw))
            
        new_cols = []
        col_idx_map = {} # ★ 원본 엑셀에서의 '특이사항', '조치현황'의 정확한 열(Column) 위치 추적
        for i, c in enumerate(orig_cols):
            c_clean = str(c).replace(" ", "").upper()
            if '날짜' in c_clean or '일자' in c_clean: new_cols.append('날짜')
            elif '발행부서' in c_clean: new_cols.append('발행부서')
            elif '발행자' in c_clean or '작성자' in c_clean: new_cols.append('발행자')
            elif '장비호기' in c_clean or '호기' in c_clean: new_cols.append('장비호기')
            elif 'ECN' in c_clean or '문서번호' in c_clean: new_cols.append('ECN No')
            elif 'AS-IS' in c_clean or 'ASIS' in c_clean or '내용' in c_clean: new_cols.append('AS-IS')
            elif 'TO-BE' in c_clean or 'TOBE' in c_clean or '변경' in c_clean: new_cols.append('TO-BE')
            elif '특이사항' in c_clean or '비고' in c_clean: 
                new_cols.append('특이사항')
                col_idx_map['특이사항'] = i
            elif '조치' in c_clean or '진행' in c_clean: 
                new_cols.append('조치현황')
                col_idx_map['조치현황'] = i
            elif '첨부' in c_clean: new_cols.append('첨부')
            else: new_cols.append(str(c).strip())
        
        new_cols.append('Original_Index')
        df.columns = new_cols
        
        if '장비호기' in df.columns:
            if unit == "전체":
                filtered_df = df.copy()
            else:
                target_match = re.search(r'(\d+)호기', unit)
                target_num = int(target_match.group(1)) if target_match else -1
                
                def check_match(val):
                    if pd.isna(val): return False
                    val_str = str(val).lower()
                    
                    if unit.lower() in val_str:
                        return True
                        
                    ranges = re.findall(r'(\d+)\s*[~-]\s*(\d+)', val_str)
                    for s_str, e_str in ranges:
                        s, e = int(s_str), int(e_str)
                        if s > e: s, e = e, s
                        if s <= target_num <= e:
                            return True
                            
                    return False

                mask = df['장비호기'].apply(check_match)
                filtered_df = df[mask].copy()
        elif '발행부서' in df.columns: 
            filtered_df = df.copy()
        else:
            st.error("⚠️ 엑셀 파일 컬럼을 인식할 수 없습니다. 양식을 다시 확인해주세요.")
            st.dataframe(df, use_container_width=True)
            return
            
        expected_cols = ['Original_Index', '날짜', '발행부서', '발행자', 'ECN No', 'AS-IS', 'TO-BE', '특이사항', '조치현황', '첨부']
        display_cols = [c for c in expected_cols if c in filtered_df.columns]
        filtered_df = filtered_df[display_cols]
        
        filtered_df = filtered_df.replace(['nan', 'NaN', 'None', 'nat', 'NaT'], '')
        
        if '날짜' in filtered_df.columns:
            def parse_date_robust(d):
                if pd.isna(d) or str(d).strip() in ['', 'nan', 'NaN', 'None', 'nat', 'NaT']: 
                    return pd.NaT
                d_str = str(d).strip()
                
                if d_str.replace('.', '', 1).isdigit():
                    val = float(d_str)
                    if 30000 < val < 80000: 
                        return pd.to_datetime(val, unit='D', origin='1899-12-30')
                
                try: 
                    d_str_clean = d_str.replace('.', '-').replace('/', '-')
                    return pd.to_datetime(d_str_clean, errors='coerce')
                except:
                    return pd.NaT
                    
            filtered_df['TempDate'] = filtered_df['날짜'].apply(parse_date_robust)
            filtered_df = filtered_df.dropna(subset=['TempDate'])
            filtered_df = filtered_df.sort_values(by='TempDate', ascending=False)
            filtered_df['날짜'] = filtered_df['TempDate'].dt.strftime('%Y-%m-%d')
            filtered_df = filtered_df.drop(columns=['TempDate'])
            
        filtered_df = filtered_df.fillna("")
        
        if not filtered_df.empty:
            # ★ 조치현황, 특이사항 제외한 나머지 컬럼은 수정 불가능하게 설정
            disabled_cols = [c for c in filtered_df.columns if c not in ['특이사항', '조치현황']]
            
            st.info("✏️ 표의 **'조치현황'** 과 **'특이사항'** 칸을 더블 클릭하여 내용을 직접 수정할 수 있습니다. 수정한 뒤엔 아래 저장 버튼을 꼭 눌러주세요.")
            
            # ★ st.data_editor 로 데이터프레임을 편집 가능하게 오픈!
            edited_df = st.data_editor(
                filtered_df, 
                use_container_width=True, 
                hide_index=True,
                disabled=disabled_cols,
                column_config={
                    "Original_Index": None, # 화면에 안보이게 숨김 처리
                    "AS-IS": st.column_config.TextColumn("AS-IS", width="large"),
                    "TO-BE": st.column_config.TextColumn("TO-BE", width="large"),
                    "특이사항": st.column_config.TextColumn("특이사항", width="medium"),
                    "조치현황": st.column_config.TextColumn("조치현황", width="medium"),
                    "첨부": st.column_config.TextColumn("첨부(복사)", width="small")
                }
            )
            
            # ★ 변경사항 자동 저장 시스템 (양식/포맷 완벽 보존)
            if st.button("💾 ECN/STN 변경사항 엑셀에 자동 저장하기", type="primary"):
                try:
                    # openpyxl을 통해 엑셀을 열어서 원본 테두리, 색상 등을 유지한 채 딱 글자만 바꿈
                    wb = openpyxl.load_workbook(io.BytesIO(raw_bytes))
                    ws = wb[first_sheet]
                    
                    changes_made = False
                    for _, row in edited_df.iterrows():
                        orig_idx = int(row['Original_Index'])
                        xl_row = orig_idx + 1 # 엑셀은 1번 줄부터 시작하므로 +1
                        
                        if '특이사항' in col_idx_map:
                            xl_col = col_idx_map['특이사항'] + 1
                            ws.cell(row=xl_row, column=xl_col, value=row['특이사항'])
                            changes_made = True
                            
                        if '조치현황' in col_idx_map:
                            xl_col = col_idx_map['조치현황'] + 1
                            ws.cell(row=xl_row, column=xl_col, value=row['조치현황'])
                            changes_made = True
                            
                    if changes_made:
                        output = io.BytesIO()
                        wb.save(output)
                        repo.update_file(target_file, f"Dashboard Update: ECN ({equipment}-{unit})", output.getvalue(), file_content.sha)
                        st.success("✅ 엑셀 원본 파일에 성공적으로 저장되었습니다! 화면을 새로고침 합니다.")
                        st.rerun()
                    else:
                        st.warning("저장할 변경사항이 없습니다.")
                except Exception as save_err:
                    st.error(f"엑셀 저장 중 오류가 발생했습니다: {save_err}")
        else:
            st.warning(f"선택하신 [{equipment}] - [{unit}] 에 등록된 유효한 ECN & STN 내역이 없습니다. (날짜가 입력된 내역만 표출됩니다.)")
            
    except Exception as e:
        if "404" in str(e):
            st.error(f"⚠️ 깃허브에 **`{target_file}`** 파일이 없습니다. 엑셀 양식을 만들어 업로드해주세요.")
        else:
            st.error(f"⚠️ 파일을 읽는 중 오류가 발생했습니다: {e}")

# ==========================================
# 7. 메인 실행 
# ==========================================
def main():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"]); repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except Exception as e:
        st.error(f"⚠️ 깃허브 연결 설정 오류: {e}")
        return

    if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user_name': ""})

    if not st.session_state['logged_in']:
        with st.form("login"):
            name = st.text_input("성함"); 
            if st.form_submit_button("입장") and name: 
                st.session_state.update({'logged_in': True, 'user_name': name}); st.rerun()
    else:
        top_col1, top_col2, top_col3 = st.columns([6, 3, 1])
        with top_col2:
            menu_selection = st.selectbox("📂 대시보드 메뉴 이동", ["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터", "🛠️ ECN & STN"], label_visibility="collapsed")
        with top_col3:
            if st.button("🚪 로그아웃", use_container_width=True): 
                st.session_state['logged_in'] = False
                st.rerun()

        st.sidebar.markdown(f"👤 **{st.session_state['user_name']}** 님 환영합니다.")

        if menu_selection == "📝 업무일지": render_work_log_page(db_log)
        elif menu_selection == "✅ CS 작업체크시트": render_cs_flow_page(db_flow)
        elif menu_selection == "📊 장비가동데이터": render_equipment_data_page(repo)
        elif menu_selection == "🛠️ ECN & STN": render_ecn_stn_page(repo)

if __name__ == "__main__": main()
