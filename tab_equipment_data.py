import streamlit as st
import pandas as pd
import io
import re
import calendar
from datetime import datetime, date
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import EQUIPMENT_OPTIONS

class EquipmentDataTab:
    def __init__(self, repo):
        self.repo = repo

    def render(self):
        st.markdown("<div class='main-title'>📊 장비 가동 데이터 정밀 분석</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1: equipment = st.selectbox("장비 선택", EQUIPMENT_OPTIONS, key="eq_data_equip")
        with col2: unit = st.selectbox("호기 선택", [f"{i}호기" for i in range(1, 16)], key="eq_data_unit")
        
        today = datetime.today().date()
        with col3: 
            date_range = st.date_input("📅 조회 기간 선택 (시작일과 종료일을 클릭하세요)", [today.replace(day=1), today])

        if len(date_range) == 2:
            s_date, e_date = date_range
        else:
            s_date = e_date = date_range[0]

        periods = pd.period_range(s_date.replace(day=1), e_date, freq='M')
        ym_list = [(p.year, p.month) for p in periods]
        month_dict = {i: eng for i, eng in enumerate(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], start=1)}
        
        all_cdf = []
        all_cl = []
        missing_files = []

        for y, m in ym_list:
            eng_month = month_dict.get(m, "January")
            
            # ★ 4단계 스마트 탐색
            file_candidates = [
                f"data/{equipment}/{equipment}_{unit} - {eng_month} {y}.xlsx",
                f"data/{equipment}/{equipment} - {eng_month} {y}.xlsx",
                f"{equipment}_{unit} - {eng_month} {y}.xlsx",
                f"{equipment} - {eng_month} {y}.xlsx"
            ]
            
            target_file = file_candidates[0]
            file_content = None
            
            for cand in file_candidates:
                try:
                    file_content = self.repo.get_contents(cand)
                    target_file = cand
                    break
                except:
                    continue
                    
            if file_content is None:
                missing_files.append(file_candidates[0])
                continue

            try:
                excel_data = io.BytesIO(file_content.decoded_content)
                xls = pd.read_excel(excel_data, sheet_name=None, header=None, engine='openpyxl')
                
                # ★ 해결 1: 특정 글자를 못 찾아도 에러 안 나게, 무조건 첫 번째 시트를 강제 기본값으로 설정!
                df_raw = list(xls.values())[0] 
                for _, data in xls.items():
                    if data.astype(str).apply(lambda r: r.str.contains('Unit|Output', case=False).any(), axis=1).any():
                        df_raw = data; break
                
                def get_sum_row(keywords):
                    for _, row in df_raw.iterrows():
                        # ★ 해결 2: join 에러 방지를 위해 map(str) 사용
                        rs = "".join(map(str, row.tolist())).lower().replace(" ", "").replace("#", "").replace("_", "")
                        if any(k in rs for k in keywords) and not any(x in rs for x in ['%', '발생률', 'rate']):
                            vals = row.tolist()
                            for i, v in enumerate(vals):
                                if str(v).replace('.','').isdigit() or str(v) in ['비가동', '미가동']: return (vals[i:i+31]+[0]*31)[:31]
                    return [0]*31

                u_vals = get_sum_row(['totalunit', 'output'])
                j_vals = get_sum_row(['jamcount', 'jam'])
                p_vals = get_sum_row(['ppj'])
                
                _, last_day = calendar.monthrange(y, m)
                month_dates = [date(y, m, d) for d in range(1, last_day + 1)]
                
                cdf = pd.DataFrame({
                    'DateObj': month_dates,
                    '날짜': [f"{str(y)[-2:]}.{m}/{d}" for d in range(1, last_day + 1)],
                    'Unit': u_vals[:last_day],
                    'Jam': j_vals[:last_day],
                    'PPJ': p_vals[:last_day]
                })
                all_cdf.append(cdf)

                h_idx = -1
                for i, r in df_raw.iterrows():
                    # ★ 해결 3: join 에러 완벽 차단
                    rs = "".join(map(str, r.tolist())).lower().replace(" ", "")
                    if 'errorcode' in rs or '에러코드' in rs or '코드' in rs:
                        h_idx = i
                        break
                
                if h_idx == -1:
                    continue 

                sh = ["".join([str(df_raw.iloc[h_idx+o, cidx]).lower().replace(" ", "") for o in [-1,0,1] if 0 <= h_idx+o < len(df_raw)]) for cidx in range(len(df_raw.columns))]
                m_col = {'D': -1, 'C': -1, 'M': -1, 'A': -1, 'T': -1, 'L': -1, 'P': -1}
                for i, vs in enumerate(sh):
                    if m_col['D']==-1 and ('date' in vs or '일자' in vs or '날짜' in vs): m_col['D']=i
                    elif m_col['C']==-1 and ('errorcode' in vs or '에러코드' in vs or '코드' in vs): m_col['C']=i
                    elif m_col['M']==-1 and ('massage' in vs or 'message' in vs or '내용' in vs): m_col['M']=i
                    elif m_col['A']==-1 and ('finding' in vs or 'action' in vs or '조치' in vs): m_col['A']=i
                    elif m_col['T']==-1 and ('time' in vs or '시간' in vs): m_col['T']=i
                    elif m_col['L']==-1 and ('point' in vs or '위치' in vs): m_col['L']=i
                    elif m_col['P']==-1 and ('ppj' in vs or '효율' in vs): m_col['P']=i
                if m_col['P']==-1 and m_col['M']!=-1: m_col['P']=m_col['M']-1
                
                def is_meaningful(val):
                    if pd.isna(val): return False
                    vs = str(val).strip().lower()
                    if vs in ['nan', 'none', 'null', 'nat', '', '0', '0.0']: return False
                    return len(re.sub(r'[^a-zA-Z0-9가-힣]', '', vs)) > 0

                def clean_val(val):
                    vs = str(val).strip()
                    return "" if pd.isna(val) or vs.lower() in ['nan', 'none', 'null', 'nat', '0.0'] else vs

                current_dt_obj = None
                current_ppj_val = "0"
                for _, r in df_raw.iloc[h_idx+1:].iterrows():
                    raw_c = r.iloc[m_col['C']] if m_col['C'] != -1 else None
                    raw_m = r.iloc[m_col['M']] if m_col['M'] != -1 else None
                    if not is_meaningful(raw_c) and not is_meaningful(raw_m): continue
                        
                    raw_d = r.iloc[m_col['D']] if m_col['D'] != -1 else None
                    
                    if is_meaningful(raw_d):
                        try: 
                            if str(raw_d).replace('.','').isdigit(): 
                                current_dt_obj = pd.to_datetime(float(raw_d), unit='D', origin='1899-12-30').date()
                            else: 
                                current_dt_obj = pd.to_datetime(str(raw_d).split(' ')[0].replace('.', '-')).date()
                        except: pass
                    
                    if current_dt_obj is None or not (s_date <= current_dt_obj <= e_date):
                        continue

                    raw_p = r.iloc[m_col['P']] if m_col['P'] != -1 else None
                    if is_meaningful(raw_p):
                        current_ppj_val = clean_val(raw_p).split('.')[0]
                    
                    time_val = clean_val(r.iloc[m_col['T']] if m_col['T'] != -1 else None)
                    if ':' not in time_val and '.' in time_val: time_val = time_val.split('.')[0]

                    code_val = clean_val(raw_c)
                    if code_val.endswith('.0'): code_val = code_val[:-2]

                    all_cl.append({
                        "DateObj": current_dt_obj,
                        "Date": current_dt_obj.strftime('%Y-%m-%d'), 
                        "Time": time_val,
                        "Code": code_val,
                        "PPJ": current_ppj_val, 
                        "Msg": clean_val(raw_m), 
                        "Act": clean_val(r.iloc[m_col['A']] if m_col['A'] != -1 else None), 
                        "Loc": clean_val(r.iloc[m_col['L']] if m_col['L'] != -1 else None)
                    })

            except Exception as e:
                if "404" in str(e):
                    missing_files.append(target_file)
                continue

        if missing_files:
            st.warning(f"⚠️ 선택하신 기간 중 깃허브에 존재하지 않는 파일이 있습니다:\n" + "\n".join([f"- {f}" for f in missing_files]))

        if not all_cdf:
            st.error("데이터를 찾지 못했습니다. 깃허브에 해당 월의 엑셀 파일이 있는지 다시 한 번 확인해 주세요.")
            return

        final_cdf = pd.concat(all_cdf).reset_index(drop=True)
        mask = (final_cdf['DateObj'] >= s_date) & (final_cdf['DateObj'] <= e_date)
        final_cdf = final_cdf[mask].reset_index(drop=True)
        
        if final_cdf.empty:
            st.warning("선택하신 조회 기간에 기록 가동 데이터가 없습니다.")
            return

        for c in ['Unit', 'Jam', 'PPJ']: 
            final_cdf[c] = pd.to_numeric(final_cdf[c].astype(str).str.replace(',', '').replace(['nan','비가동','None',''], '0'), errors='coerce').fillna(0)
        
        final_cdf['Cum_PPJ'] = final_cdf.apply(lambda r: round(final_cdf.loc[:r.name, 'Unit'].sum() / final_cdf.loc[:r.name, 'Jam'].sum(), 1) if final_cdf.loc[:r.name, 'Jam'].sum() > 0 else 0, axis=1)
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15, 
                            subplot_titles=("Unit 및 Jam 건수 (보조축 적용)", "생산 효율(PPJ)"), 
                            specs=[[{"secondary_y": True}], [{"secondary_y": False}]])
        
        fig.add_trace(go.Bar(x=final_cdf['날짜'], y=final_cdf['Unit'], name='투입', marker_color='#5B9BD5', legendgroup="1", hovertemplate="%{x}<br>투입: %{y:,.0f}<extra></extra>"), row=1, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=final_cdf['날짜'], y=final_cdf['Jam'], name='에러', mode='lines+markers', line=dict(color='#ED7D31'), legendgroup="1", hovertemplate="%{x}<br>에러: %{y:,.0f}<extra></extra>"), row=1, col=1, secondary_y=True)
        
        fig.add_trace(go.Bar(x=final_cdf['날짜'], y=final_cdf['PPJ'], name='일별PPJ', marker_color='#A9D18E', legendgroup="2", hovertemplate="%{x}<br>일별 PPJ: %{y:,.1f}<extra></extra>"), row=2, col=1)
        fig.add_trace(go.Scatter(x=final_cdf['날짜'], y=final_cdf['Cum_PPJ'], name='누적PPJ', mode='lines+markers', line=dict(color='#FF0000', width=4), legendgroup="2", hovertemplate="%{x}<br>누적 PPJ: %{y:,.1f}<extra></extra>"), row=2, col=1)
        
        fig.update_yaxes(title_text="투입량 (EA)", secondary_y=False, row=1, col=1, tickformat="d", exponentformat="none")
        fig.update_yaxes(title_text="Jam (건)", secondary_y=True, row=1, col=1, tickformat="d", exponentformat="none")
        fig.update_yaxes(title_text="PPJ", row=2, col=1, tickformat=".1f")

        fig.update_layout(
            height=650, 
            margin=dict(l=50, r=50, t=60, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0, bgcolor="rgba(0,0,0,0)"),
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader(f"📋 에러 상세 분석 통합 리스트")
        if all_cl:
            fdf = pd.DataFrame(all_cl)
            fdf = fdf.sort_values(by=["DateObj", "Time"], ascending=[False, False], na_position='last').reset_index(drop=True)
            
            fdf['Date'] = fdf['Date'].ffill()
            fdf['PPJ'] = fdf['PPJ'].ffill().fillna("0")
            
            html = "".join([f"<tr><td style='width:75px;'>{r['Date'] if not pd.isna(r['Date']) else ''}</td><td style='width:60px;'>{r.get('Code', '')}</td><td style='width:60px;'>{r['PPJ']}</td><td class='t-left'>{r['Msg']}</td><td class='t-left'>{r['Act']}</td><td style='width:65px;'>{r['Time']}</td><td style='width:90px;'>{r['Loc']}</td></tr>" for _, r in fdf.iterrows()])
            st.markdown(f"<table class='final-report-table'><thead><tr><th style='width:75px;'>날짜</th><th style='width:60px;'>코드</th><th style='width:60px;'>PPJ</th><th>에러내용</th><th>조치내용</th><th style='width:65px;'>시간</th><th style='width:90px;'>위치</th></tr></thead><tbody>{html}</tbody></table>", unsafe_allow_html=True)
        else:
            st.info("선택하신 기간 내 상세 에러 내역이 없습니다.")
