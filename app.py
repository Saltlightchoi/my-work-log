import streamlit as st
import pandas as pd
from github import Github
import io
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
        
        /* 탭 디자인 커스텀 */
        button[data-baseweb="tab"] { font-size: 18px !important; font-weight: bold !important; }
        
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

EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

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

def get_row_color(row):
    val = row.get('상태', '')
    if val == '✅ 완료': return ['background-color: rgba(76, 175, 80, 0.2)'] * len(row)
    elif val == '⏳ 작업중': return ['background-color: rgba(255, 193, 7, 0.2)'] * len(row)
    elif val == '🚨 보류': return ['background-color: rgba(244, 67, 54, 0.2)'] * len(row)
    return [''] * len(row)

# ==========================================
# 3. 탭 1: 팀 업무일지 (복구 및 통합)
# ==========================================
def render_work_log_page(db_log):
    df_log, sha_log = db_log.load()
    if not df_log.empty and '날짜' in df_log.columns:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)

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

    st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    search = st.text_input("🔍 검색어 (장비, 내용 등)", placeholder="검색어를 입력하세요...")
    disp = df_log.copy()
    if search: disp = disp[disp.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(disp, use_container_width=True, hide_index=True, column_config={"업무내용": st.column_config.TextColumn("업무내용", width="large")})

# ==========================================
# 4. 탭 2: CS 작업체크시트 (배터리/색상/프로젝트 관리 복구)
# ==========================================
def render_cs_flow_page(db_flow):
    df_flow, sha_flow = db_flow.load()
    st.markdown("<div class='main-title'>✅ CS 작업 체크 시트</div>", unsafe_allow_html=True)
    
    project_list = df_flow["프로젝트명"].unique().tolist() if not df_flow.empty else []
    
    # 배터리 진척도 계산 로직
    progress_dict = {}
    for proj in project_list:
        p_df = df_flow[df_flow["프로젝트명"] == proj]
        comp = len(p_df[p_df["상태"] == "✅ 완료"])
        total = len(p_df)
        pct = int((comp / total) * 100) if total > 0 else 0
        bar = "🟩" * (pct // 10) + "⬜" * (10 - (pct // 10))
        progress_dict[proj] = f"{proj} | {'🔋' if pct >= 20 else '🪫'} {pct}% [{bar}]"

    col_sel, col_btn = st.columns([7, 3])
    with col_sel:
        selected_proj = st.selectbox("📌 프로젝트 선택", project_list, format_func=lambda x: progress_dict.get(x, x))
    with col_btn:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        save_btn = st.button("💾 전체 변경사항 저장", use_container_width=True)

    if selected_proj:
        proj_df = df_flow[df_flow["프로젝트명"] == selected_proj].copy()
        proj_df['group_id'] = (proj_df['대항목'] != proj_df['대항목'].shift()).cumsum()
        
        edited_list = []
        for g_id, g_df in proj_df.groupby('group_id', sort=False):
            cat = g_df['대항목'].iloc[0]
            statuses = g_df['상태'].tolist()
            icon = "🟢" if all(s == "✅ 완료" for s in statuses) else "🟡" if any(s in ["⏳ 작업중", "✅ 완료"] for s in statuses) else "⚪"
            
            with st.expander(f"{icon} 대항목: {cat}", expanded=True):
                edited = st.data_editor(
                    g_df.drop(columns=['group_id']).style.apply(get_row_color, axis=1),
                    use_container_width=True, hide_index=True, key=f"cs_{selected_proj}_{g_id}",
                    column_config={
                        "작업내용": st.column_config.TextColumn("세부작업", width="large"),
                        "상태": st.column_config.SelectboxColumn("상태", options=["⬜ 대기", "⏳ 작업중", "✅ 완료", "🚨 보류"], width="small")
                    }
                )
                # 업데이트일 자동 기록
                for idx, row in edited.iterrows():
                    if row['상태'] != g_df.iloc[idx]['상태'] and row['상태'] != "⬜ 대기":
                        edited.at[idx, '업데이트일'] = f"{st.session_state['user_name']} ({datetime.now().strftime('%y-%m-%d')})"
                edited_list.append(edited)

        if save_btn:
            new_proj_df = pd.concat(edited_list)
            other_projs = df_flow[df_flow["프로젝트명"] != selected_proj]
            db_flow.save(pd.concat([other_projs, new_proj_df], ignore_index=True), sha_flow, f"Update: {selected_proj}")
            st.success("저장되었습니다!"); st.rerun()

# ==========================================
# 5. 탭 3: 장비 가동 데이터 (2단 그래프/보조축/테두리 표)
# ==========================================
def render_equipment_data_page():
    st.markdown("<div class='main-title'>📊 장비 가동 데이터 통합 분석</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col3: month_str = st.selectbox("조회 월 선택", ["1월", "2월", "3월"], key="eq_m")
    
    file_map = {"1월": "SLH1 - January 2026.xlsx", "2월": "SLH1 - February 2026.xlsx", "3월": "SLH1 - March 2026.xlsx"}
    target = file_map.get(month_str, "")

    try:
        xls = pd.read_excel(target, sheet_name=None, header=None, engine='openpyxl')
        df_raw = None
        for name, data in xls.items():
            if data.astype(str).apply(lambda r: r.str.contains('Unit|Output', case=False).any(), axis=1).any():
                df_raw = data; break
        
        if df_raw is None: st.info("데이터를 불러오는 중입니다..."); return

        def get_sum_row(keywords):
            for _, row in df_raw.iterrows():
                row_str = "".join(row.astype(str)).lower().replace(" ", "").replace("#", "").replace("_", "")
                if any(k in row_str for k in keywords) and not any(x in row_str for x in ['%', '발생률']):
                    vals = row.tolist()
                    for i, v in enumerate(vals):
                        if str(v).replace('.','').replace(',','').strip().isdigit(): return (vals[i:i+31]+[0]*31)[:31]
            return [0]*31

        c_df = pd.DataFrame({'날짜': [f"{month_str}/{i}" for i in range(1, 32)], 'Unit': get_sum_row(['totalunit']), 'Jam': get_sum_row(['jamcount']), 'PPJ': get_sum_row(['ppj'])})
        for c in ['Unit', 'Jam', 'PPJ']: c_df[c] = pd.to_numeric(c_df[c].astype(str).str.replace(',', '').replace(['nan','비가동',''], '0'), errors='coerce').fillna(0)

        # 📊 그래프 (상단: 보조축 적용, 하단: PPJ)
        fig = make_subplots(rows=2, cols=1, vertical_spacing=0.12, subplot_titles=("투입량(Unit) 및 Jam 현황", "생산 효율(PPJ) 추이"), specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
        fig.add_trace(go.Bar(x=c_df['날짜'], y=c_df['Unit'], name='Unit(막대)', marker_color='#5B9BD5'), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=c_df['날짜'], y=c_df['Jam'], name='Jam(선)', mode='lines+markers', line=dict(color='#ED7D31', width=2)), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=c_df['날짜'], y=c_df['PPJ'], name='PPJ(효율)', mode='lines+markers', line=dict(color='#70AD47', width=3)), row=2, col=1)
        fig.update_layout(height=600, margin=dict(l=50, r=50, t=50, b=50), hovermode="x unified")
        fig.update_yaxes(title_text="Unit (EA)", secondary_y=False, row=1, col=1)
        fig.update_yaxes(title_text="Jam (건)", secondary_y=True, row=1, col=1)
        st.plotly_chart(fig, use_container_width=True)

        # 📋 상세 리스트
        st.subheader("📋 장비 에러 상세 분석")
        h_idx = next(i for i, row in df_raw.iterrows() if 'error code' in " ".join(row.astype(str)).lower())
        h_row = df_raw.iloc[h_idx].tolist()
        m = {k: next((i for i, v in enumerate(h_row) if k in str(v).lower()), 0) for k in ['date', 'error code', 'error massage', 'finding', 'time', 'point', 'ppj']}
        
        rows_html = ""
        cur_d, cur_p = "", "0"
        for _, r in df_raw.iloc[h_idx+1:].iterrows():
            if str(r[m['error code']]).strip() in ['nan', 'None', '']: continue
            if not pd.isna(r[m['date']]): cur_d = str(r[m['date']]).split(' ')[0]
            if not pd.isna(r[m['ppj']]): cur_p = str(r[m['ppj']]).split('.')[0]
            rows_html += f"<tr><td style='width:75px;'>{cur_d}</td><td style='width:60px;'>{r[m['error code']]}</td><td style='width:50px;'>{cur_p}</td><td class='t-left'>{r[m['error massage']]}</td><td class='t-left'>{r[m['finding']]}</td><td style='width:65px;'>{str(r[m['time']]).split('.')[0]}</td><td>{r[m['point']]}</td></tr>"
        st.markdown(f"<table class='final-report-table'><thead><tr><th>날짜</th><th>코드</th><th>PPJ</th><th>내용</th><th>조치</th><th>시간</th><th>위치</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
    except: st.info("파일을 분석 중입니다...")

# ==========================================
# 6. 메인 실행
# ==========================================
def main():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "업데이트일", "첨부"])
    except: return

    if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user_name': ""})
    if not st.session_state['logged_in']:
        with st.form("login"):
            name = st.text_input("성함 입력")
            if st.form_submit_button("입장하기") and name:
                st.session_state.update({'logged_in': True, 'user_name': name}); st.rerun()
    else:
        t1, t2, t3 = st.tabs(["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터"])
        with t1: render_work_log_page(db_log)
        with t2: render_cs_flow_page(db_flow)
        with t3: render_equipment_data_page()

if __name__ == "__main__": main()
