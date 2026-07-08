import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import DataManager
import datetime

class EquipmentDataTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📊 장비 가동 정밀 데이터 분석")
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
        
        DB_SHEET_OPTIONS = ["SLH1 #1", "SLH1 #4", "SLH1 #5", "SLH1 #6", "SLH1 #7"]
        
        col1, col2 = st.columns([2, 8])
        with col1:
            equip_val = st.selectbox("분석할 장비 선택", DB_SHEET_OPTIONS)

        # ==========================================
        # 1. Jam 데이터 로드
        # ==========================================
        target_tab = "SLH1 #1" if equip_val == "SLH1 #1" else equip_val
            
        exact_columns = [
            "Date", "Totalunit", "Errorcode", "Errorcount", "Error Masage", 
            "현상", "원인", "조치", "Err.Point", "분류", "조치자", "Err. Time", 
            "MTBA", "MTTR", "MTBI", "도번", "수량", "입고일", "반입일", "조치위치", "조치결과"
        ]
        
        try:
            db_machine = DataManager(self.db_jam.spreadsheet_id, target_tab, exact_columns)
            df, _ = db_machine.load()
        except Exception as e:
            st.error(f"🚨 데이터 로드 실패: {e}")
            return
            
        if df.empty:
            st.info(f"💡 '{equip_val}' 장비 데이터가 없습니다.")
            return

        # ==========================================
        # 2. 데이터 전처리
        # ==========================================
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date']).sort_values('Date')
        
        numeric_cols = ['Totalunit', 'Errorcount', 'MTBA', 'MTTR', 'MTBI']
        for c in numeric_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        # 조회 기간(날짜) 선택 필터
        min_date = df['Date'].min().date()
        max_date = df['Date'].max().date()
        
        with col2:
            default_start = max_date - datetime.timedelta(days=30)
            if default_start < min_date: 
                default_start = min_date
                
            date_range = st.date_input(
                "📅 조회 기간 선택", 
                value=(default_start, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
        if len(date_range) == 2:
            start_date, end_date = date_range
        elif len(date_range) == 1:
            start_date = date_range[0]
            end_date = date_range[0]
        else:
            st.warning("날짜를 선택해주세요.")
            return
            
        mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
        df_filtered = df.loc[mask]

        date_title_str = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

        # ✅ [핵심 해결] 시작일~종료일 사이의 '모든 달력 날짜'를 강제로 생성합니다.
        full_date_range = pd.date_range(start=start_date, end=end_date).date

        # ==========================================
        # 3. 상단: 생산 Unit 대비 Jam 발생 & PPJ 누적 그래프
        # ==========================================
        st.markdown(f"#### 📊 {date_title_str} 기본 가동 현황 (PPJ 및 생산대비 Jam)")
        
        # 날짜별 그룹화 후, full_date_range(전체 날짜)를 기준으로 뼈대를 다시 맞추고 빈칸을 0으로 채웁니다.
        df_daily_basic = df_filtered.groupby(df_filtered['Date'].dt.date).agg({
            'Totalunit': 'max',
            'Errorcount': 'sum'
        }).reindex(full_date_range).fillna(0).reset_index()
        
        # 컬럼명 정리 및 문자열 변환
        df_daily_basic.rename(columns={'index': 'Date'}, inplace=True)
        df_daily_basic['Date'] = pd.to_datetime(df_daily_basic['Date'])
        df_daily_basic['DateStr'] = df_daily_basic['Date'].dt.strftime('%m/%d')

        # 누적합 계산 (빈 날짜의 0도 누적에 그대로 반영되어 평행선 유지)
        df_daily_basic['Cum_Totalunit'] = df_daily_basic['Totalunit'].cumsum()
        df_daily_basic['Cum_Errorcount'] = df_daily_basic['Errorcount'].cumsum()

        # PPJ 계산
        df_daily_basic['PPJ'] = df_daily_basic.apply(
            lambda row: row['Totalunit'] / row['Errorcount'] if row['Errorcount'] > 0 else row['Totalunit'], 
            axis=1
        )
        df_daily_basic['Cum_PPJ'] = df_daily_basic.apply(
            lambda row: row['Cum_Totalunit'] / row['Cum_Errorcount'] if row['Cum_Errorcount'] > 0 else row['Cum_Totalunit'], 
            axis=1
        )

        col_top1, col_top2 = st.columns(2)
        
        # [그래프 1] 생산 Unit 대비 Jam 발생
        with col_top1:
            fig_tu = make_subplots(specs=[[{"secondary_y": True}]])
            
            # ✅ 값이 0이어도 수치가 "0"으로 정직하게 표출되도록 조건식 제거
            fig_tu.add_trace(
                go.Scatter(
                    x=df_daily_basic['DateStr'], y=df_daily_basic['Totalunit'], 
                    mode='lines+markers+text', name='생산량', line=dict(color='#3498DB', width=3),
                    text=df_daily_basic['Totalunit'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                    textposition='top left', textfont=dict(size=12) 
                ), secondary_y=False
            )
            fig_tu.add_trace(
                go.Scatter(
                    x=df_daily_basic['DateStr'], y=df_daily_basic['Errorcount'], 
                    mode='lines+markers+text', name='Jam 발생', line=dict(color='#E74C3C', width=3),
                    text=df_daily_basic['Errorcount'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                    textposition='top right', textfont=dict(size=12) 
                ), secondary_y=True
            )
            
            fig_tu.update_layout(title="생산량 대비 Jam 발생", margin=dict(l=20, r=20, t=40, b=20), height=400, hovermode="x unified")
            fig_tu.update_xaxes(type='category')
            
            max_tu = df_daily_basic['Totalunit'].max()
            max_err = df_daily_basic['Errorcount'].max()
            fig_tu.update_yaxes(title_text="생산량", secondary_y=False, range=[0, max_tu * 1.2 if max_tu > 0 else 10])
            fig_tu.update_yaxes(title_text="Jam 건수", secondary_y=True, range=[0, max_err * 1.2 if max_err > 0 else 10])
            
            st.plotly_chart(fig_tu, use_container_width=True, theme="streamlit")

        # [그래프 2] 일별 PPJ 및 누적 평균 PPJ
        with col_top2:
            fig_ppj = go.Figure()
            
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['DateStr'], y=df_daily_basic['PPJ'], 
                mode='lines+markers+text', name='일별 PPJ', line=dict(color='#27AE60', width=3),
                text=df_daily_basic['PPJ'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                textposition='top left', textfont=dict(size=12)
            ))
            
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['DateStr'], y=df_daily_basic['Cum_PPJ'], 
                mode='lines+markers+text', name='누적 평균 PPJ', line=dict(color='#F39C12', width=3),
                text=df_daily_basic['Cum_PPJ'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                textposition='top right', textfont=dict(size=12)
            ))
            
            fig_ppj.update_layout(title="일별 PPJ 및 누적 평균 PPJ", margin=dict(l=20, r=20, t=40, b=20), height=400, hovermode="x unified")
            fig_ppj.update_xaxes(type='category')
            
            max_ppj = max(df_daily_basic['PPJ'].max(), df_daily_basic['Cum_PPJ'].max())
            fig_ppj.update_yaxes(dtick=2500, tickformat=",", range=[0, max_ppj * 1.2 if max_ppj > 0 else 10])
            
            st.plotly_chart(fig_ppj, use_container_width=True, theme="streamlit")

        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # ==========================================
        # 4. 하단: 정밀 분석 추이 (MTBA / MTTR / MTBI)
        # ==========================================
        st.markdown(f"#### 📈 {date_title_str} 정밀 분석 추이 (MTBA / MTTR / MTBI)")
        
        # ✅ MT 데이터 역시 빈 날짜를 0으로 강제 세팅합니다.
        df_daily_mt = df_filtered.groupby(df_filtered['Date'].dt.date)[['MTBA', 'MTTR', 'MTBI']].max().reindex(full_date_range).fillna(0).reset_index()
        df_daily_mt.rename(columns={'index': 'Date'}, inplace=True)
        df_daily_mt['Date'] = pd.to_datetime(df_daily_mt['Date'])
        df_daily_mt['DateStr'] = df_daily_mt['Date'].dt.strftime('%m/%d')
        
        for col in ['MTBA', 'MTTR', 'MTBI']:
            df_daily_mt[f'{col}_cum_avg'] = df_daily_mt[col].expanding().mean()
            
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

        metrics = [
            ('MTBA', '#AED6F1', '#2E86C1'), 
            ('MTTR', '#F5B7B1', '#E74C3C'), 
            ('MTBI', '#A9DFBF', '#27AE60')
        ]

        for col, bar_color, line_color in metrics:
            fig1.add_trace(go.Bar(
                x=df_daily_mt['DateStr'], y=df_daily_mt[col], 
                name=f'{col} (일별)', marker_color=bar_color,
                text=df_daily_mt[col].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                textposition='outside', textfont=dict(size=12)
            ), secondary_y=False)
            
            fig1.add_trace(go.Scatter(
                x=df_daily_mt['DateStr'], y=df_daily_mt[f'{col}_cum_avg'], 
                mode='lines+markers+text', name=f'{col} 누적평균', 
                line=dict(color=line_color, width=2),
                text=df_daily_mt[f'{col}_cum_avg'].apply(lambda x: f"<b>{x:,.1f}</b>"), 
                textposition='top right', textfont=dict(size=12)
            ), secondary_y=True)
        
        fig1.update_layout(
            height=500, 
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",
            barmode='group', 
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        fig1.update_xaxes(type='category')
        
        max_mt_daily = df_daily_mt[['MTBA', 'MTTR', 'MTBI']].max().max()
        max_mt_cum = df_daily_mt[['MTBA_cum_avg', 'MTTR_cum_avg', 'MTBI_cum_avg']].max().max()
        fig1.update_yaxes(title_text="일별 측정 수치", secondary_y=False, range=[0, max_mt_daily * 1.2 if max_mt_daily > 0 else 10])
        fig1.update_yaxes(title_text="누적 평균 수치", secondary_y=True, showgrid=False, range=[0, max_mt_cum * 1.2 if max_mt_cum > 0 else 10])
        
        st.plotly_chart(fig1, use_container_width=True, theme="streamlit")

        st.markdown("<br>", unsafe_allow_html=True)

        # 에러 발생 모듈(파이) & 분류별 발생 건수(가로바)
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### 🍩 에러 발생 모듈 (Err.Point) 점유율")
            err_point_counts = df_filtered.groupby('Err.Point')['Errorcount'].sum().reset_index()
            err_point_counts = err_point_counts[(err_point_counts['Err.Point'] != "") & (err_point_counts['Errorcount'] > 0)]
            
            if not err_point_counts.empty:
                fig2 = go.Figure(data=[go.Pie(labels=err_point_counts['Err.Point'], values=err_point_counts['Errorcount'], hole=.4)])
                
                fig2.update_traces(textfont_size=16)
                fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, legend=dict(font=dict(size=14)))
                st.plotly_chart(fig2, use_container_width=True, theme="streamlit")
            else:
                st.info("해당 기간에 Err.Point 데이터가 없습니다.")

        with col_g2:
            st.markdown("#### 📊 장애 분류별 발생 건수")
            type_counts = df_filtered.groupby('분류')['Errorcount'].sum().reset_index()
            type_counts = type_counts[(type_counts['분류'] != "") & (type_counts['Errorcount'] > 0)].sort_values(by='Errorcount', ascending=True)
            
            if not type_counts.empty:
                fig3 = go.Figure(data=[go.Bar(
                    y=type_counts['분류'], 
                    x=type_counts['Errorcount'], 
                    orientation='h', 
                    marker_color='#F39C12',
                    text=type_counts['Errorcount'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                    textposition='outside', 
                    textfont=dict(size=14) 
                )])
                max_type = type_counts['Errorcount'].max()
                fig3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="발생 건수", yaxis=dict(tickfont=dict(size=13)))
                fig3.update_xaxes(range=[0, max_type * 1.2 if max_type > 0 else 10])
                st.plotly_chart(fig3, use_container_width=True, theme="streamlit")
            else:
                st.info("해당 기간에 분류 데이터가 없습니다.")
