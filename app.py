import streamlit as st
import pandas as pd
from github import Github
import io
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 환경 설정 및 기본 상수
# ==========================================
st.set_page_config(layout="wide", page_title="장비 관리 통합 시스템")
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
        [data-testid="stSidebar"] { width: 330px !important; }
        .main-title { font-size: 1.5rem !important; font-weight: bold; padding-bottom: 10px !important; }
        
        /* 표 가독성 극대화 (진한 테두리) */
        .report-table {
            width: 100%; border-collapse: collapse; border: 2px solid #000000;
            font-size: 12px; color: #000000; background-color: #ffffff;
        }
        .report-table th, .report-table td {
            border: 1px solid #000000 !important; padding: 6px 8px; text-align: center;
        }
        .report-table th { background-color: #d9e1f2 !important; font-weight: bold; }
        .t-left { text-align: left !important; }
        
        /* 탭 디자인 */
        button[data-baseweb="tab"] { font-size: 18px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

EQUIPMENT_OPTIONS = ["SLH1", "4010H", "3208H", "3208AT", "3208M", "3208C", "3208CM", "3208XM", "ADC200", "ADC300", "ADC400", "AH5200", "AM5"]

# ==========================================
# 2. 데이터 관리 클래스
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

# ==========================================
# 3. 화면 UI - 탭 3: 장비 가동 데이터 (최종 해결본)
# ==========================================
def render_equipment_data_page():
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
            if data.astype(str).apply(lambda r: r.str.contains('Unit|Output', case=False).any(), axis=1).any():
                df_raw = data; break
        
        if df_raw is None:
            st.error("⚠️ 가동 데이터를 찾을 수 없습니다."); return

        # 요약 데이터 추출
        def get_sum_row(keywords):
            for _, row in df_raw.iterrows():
                row_str = "".join(row.astype(str)).lower().replace(" ", "").replace("#", "").replace("_", "")
                if any(k in row_str for k in keywords) and not any(x in row_str for x in ['%', '발생률']):
                    vals = row.tolist()
                    for i, v in enumerate(vals):
                        if str(v).replace('.','').replace(',','').strip().isdigit(): return (vals[i:i+31]+[0]*31)[:31]
            return [0]*31

        u_vals = get_sum_row(['totalunit', 'output'])
        j_vals = get_sum_row(['jamcount', 'jam'])
        p_vals = get_sum_row(['ppj'])

        chart_df = pd.DataFrame({'날짜': [f"{month_num}/{i}" for i in range(1, 32)], 'Unit': u_vals, 'Jam': j_vals, 'PPJ': p_vals})
        for c in ['Unit', 'Jam', 'PPJ']:
            chart_df[c] = pd.to_numeric(chart_df[c].astype(str).str.replace(',', '').replace(['nan','비가동','미가동',''], '0'), errors='coerce').fillna(0)

        # 📊 그래프 (상단: Unit/Jam(보조축), 하단: PPJ)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                            subplot_titles=("투입량(Unit) & 에러(Jam) 현황", "생산 효율(PPJ)"),
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]])

        # 위: Unit (Bar)
        fig.add_trace(go.Bar(x=chart_df['날짜'], y=chart_df['Unit'], name='Unit', marker_color='#5B9BD5'), row=1, col=1, secondary_y=False)
        # 위: Jam (Line - 보조축 사용)
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['Jam'], name='Jam', mode='lines+markers', line=dict(color='#ED7D31', width=2)), row=1, col=1, secondary_y=True)
        # 아래: PPJ (Line)
        fig.add_trace(go.Scatter(x=chart_df['날짜'], y=chart_df['PPJ'], name='PPJ', mode='lines+markers', line=dict(color='#70AD47', width=3)), row=2, col=1)

        fig.update_layout(height=600, margin=dict(l=50, r=50, t=50, b=50), hovermode="x unified", showlegend=True)
        fig.update_yaxes(title_text="Unit (EA)", secondary_y=False, row=1, col=1)
        fig.update_yaxes(title_text="Jam (건)", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="PPJ", row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

        # 📋 상세 리스트 추출
        st.subheader(f"📋 {month_str} 에러 상세 리스트")
        h_idx = -1
        for i, row in df_raw.iterrows():
            if 'error code' in " ".join(row.astype(str)).lower():
                h_idx = i; h_row = row.tolist(); break

        if h_idx != -1:
            m = {'D': 0, 'C': 0, 'M': 0, 'A': 0, 'T': 0, 'L': 0, 'P': 0}
            for i, v in enumerate(h_row):
                v_l = str(v).lower()
                if 'date' in v_l: m['D'] = i
                elif 'error code' in v_l: m['C'] = i
                elif 'error massage' in v_l: m['M'] = i
                elif 'finding' in v_l: m['A'] = i
                elif 'time' in v_l: m['T'] = i
                elif 'point' in v_l: m['L'] = i
                elif 'ppj' in v_l: m['P'] = i

            data_slice = df_raw.iloc[h_idx + 1:].copy()
            cleaned_list = []
            for _, r in data_slice.iterrows():
                code = str(r[m['C']]).strip()
                if code in ['nan', 'None', '']: continue
                
                # 날짜 처리
                dt = r[m['D']]
                if pd.isna(dt) or str(dt).strip() == 'nan': dt = None
                elif str(dt).replace('.','').isdigit():
                    dt = pd.to_datetime(float(dt), unit='D', origin='1899-12-30').strftime('%Y-%m-%d')
                else: dt = str(dt).split(' ')[0]

                ppj = str(r[m['P']]).split('.')[0] if not pd.isna(r[m['P']]) else None

                cleaned_list.append({
                    "Date": dt, "Code": code, "PPJ": ppj,
                    "Msg": str(r[m['M']]), "Act": str(r[m['A']]),
                    "Time": str(r[m['T']]).split('.')[0] if ':' in str(r[m['T']]) else str(r[m['T']]),
                    "Loc": str(r[m['L']])
                })

            if cleaned_list:
                final_df = pd.DataFrame(cleaned_list)
                final_df['Date'] = final_df['Date'].ffill()
                final_df['PPJ'] = final_df['PPJ'].ffill().fillna("0")
                
                rows_html = ""
                for _, row in final_df.iterrows():
                    rows_html += f"<tr><td style='width:75px;'>{row['Date']}</td><td style='width:60px;'>{row['Code']}</td><td style='width:60px;'>{row['PPJ']}</td><td class='t-left'>{row['Msg']}</td><td class='t-left'>{row['Act']}</td><td style='width:65px;'>{row['Time']}</td><td style='width:90px;'>{row['Loc']}</td></tr>"
                
                st.markdown(f"<table class='report-table'><thead><tr><th>날짜</th><th>코드</th><th>PPJ</th><th>에러내용</th><th>조치내용</th><th>시간</th><th>위치</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
            else: st.info("상세 데이터가 없습니다.")
        else: st.info("헤더를 찾지 못했습니다.")
    except Exception as e: st.error(f"시스템 오류: {e}")

# ==========================================
# 4. 기타 페이지들 (일지 및 체크시트)
# ==========================================
def render_work_log_page(db_log):
    st.markdown("<div class='main-title'>📝 팀 업무일지 대시보드</div>", unsafe_allow_html=True)
    df_log, sha_log = db_log.load()
    if not df_log.empty:
        df_log['날짜'] = pd.to_datetime(df_log['날짜']).dt.date.astype(str)
        df_log = df_log.sort_values(by='날짜', ascending=False).reset_index(drop=True)
    
    search = st.text_input("🔍 검색", placeholder="검색어를 입력하세요...")
    disp = df_log.copy()
    if search: disp = disp[disp.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    st.dataframe(disp, use_container_width=True, hide_index=True)

def render_cs_flow_page(db_flow):
    st.markdown("<div class='main-title'>✅ CS 작업 체크 시트</div>", unsafe_allow_html=True)
    df_flow, sha_flow = db_flow.load()
    st.info("프로젝트 관리 기능을 지원합니다.")
    st.dataframe(df_flow, use_container_width=True, hide_index=True)

# ==========================================
# 5. 메인 로직
# ==========================================
def main():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["REPO_NAME"])
        db_log = DataManager(repo, st.secrets["FILE_PATH"], ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        db_flow = DataManager(repo, "cs_flow_data.csv", ["프로젝트명", "대항목", "작업내용", "상태", "비고", "첨부", "업데이트일"])
    except:
        st.error("연결 오류")
        return

    if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'user_name': ""})
    
    if not st.session_state['logged_in']:
        with st.form("login"):
            name = st.text_input("성함")
            if st.form_submit_button("입장") and name:
                st.session_state.update({'logged_in': True, 'user_name': name})
                st.rerun()
    else:
        tab1, tab2, tab3 = st.tabs(["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터"])
        with tab1: render_work_log_page(db_log)
        with tab2: render_cs_flow_page(db_flow)
        with tab3: render_equipment_data_page()

if __name__ == "__main__":
    main()
