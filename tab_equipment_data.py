import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import DataManager
from datetime import datetime

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
            
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        available_months = sorted(df['Month'].unique(), reverse=True)
        
        if not available_months:
            st.warning("유효한 날짜 데이터가 없습니다.")
            return
            
        with col2:
            selected_month = st.selectbox("분석 월 선택", available_months)
            
        df_month = df[df['Month'] == selected_month]
        
        if df_month.empty:
            st.info("선택한 월에 해당하는 데이터가 없습니다.")
            return

        # ==========================================
        # 3. 상단: 생산 Unit 대비 Jam 발생 & PPJ 누적 그래프
        # ==========================================
        st.markdown(f"#### 📊 {selected_month} 기본 가동 현황 (PPJ 및 생산대비 Jam)")
        
        df_daily_basic = df_month.groupby(df_month['Date'].dt.date).agg({
            'Totalunit': 'max',
            'Errorcount': 'sum'
        }).reset_index()

        df_daily_basic['DateStr'] = pd.to_datetime(df_daily_basic['Date']).dt.strftime('%m/%d')
        df_daily_basic['Cum_Totalunit'] = df_daily_basic['Totalunit'].cumsum()
        df_daily_basic['Cum_Errorcount'] = df_daily_basic['Errorcount'].cumsum()

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
            
            # 텍스트에 <b> 태그를 달아 굵고 선명하게 만들고 위치를 좌측으로 배치
            fig_tu.add_trace(
                go.Scatter(
                    x=df_daily_basic['DateStr'], y=df_daily_basic['Totalunit'], 
                    mode='lines+markers+text', name='생산량', line=dict(color='#3498DB', width=3),
                    text=df_daily_basic['Totalunit'].apply(lambda x: f"<b>{x:,.0f}</b>" if x > 0 else ""), 
                    textposition='top left', textfont=dict(size=12, color='#154360') 
                ), secondary_y=False
            )
            # Jam 건수는 우측으로 배치하여 겹침 방지
            fig_tu.add_trace(
                go.Scatter(
                    x=df_daily_basic['DateStr'], y=df_daily_basic['Errorcount'], 
                    mode='lines+markers+text', name='Jam 발생', line=dict(color='#E74C3C', width=3),
                    text=df_daily_basic['Errorcount'].apply(lambda x: f"<b>{x:,.0f}</b>" if x > 0 else ""), 
                    textposition='top right', textfont=dict(size=12, color='#78281F') 
                ), secondary_y=True
            )
            
            fig_tu.update_layout(title="생산량 대비 Jam 발생", margin=dict(l=20, r=20, t=40, b=20), height=400, hovermode="x unified")
            fig_tu.update_xaxes(type='category')
            
            # ★ 천장 여유 공간 확보 (최고수치의 1.2배)
            max_tu = df_daily_basic['Totalunit'].max()
            max_err = df_daily_basic['Errorcount'].max()
            fig_tu.update_yaxes(title_text="생산량", secondary_y=False, range=[0, max_tu * 1.2 if max_tu > 0 else 10])
            fig_tu.update_yaxes(title_text="Jam 건수", secondary_y=True, range=[0, max_err * 1.2 if max_err > 0 else 10])
            
            st.plotly_chart(fig_tu, use_container_width=True)

        # [그래프 2] 일별 PPJ 및 누적 평균 PPJ
        with col_top2:
            fig_ppj = go.Figure()
            
            # 일별 PPJ (좌측 배치)
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['DateStr'], y=df_daily_basic['PPJ'], 
                mode='lines+markers+text', name='일별 PPJ', line=dict(color='#27AE60', width=3),
                text=df_daily_basic['PPJ'].apply(lambda x: f"<b>{x:,.0f}</b>" if x > 0 else ""), 
                textposition='top left', textfont=dict(size=12, color='#145A32')
            ))
            
            # 누적 PPJ (우측 배치)
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['DateStr'], y=df_daily_basic['Cum_PPJ'], 
                mode='lines+markers+text', name='누적 평균 PPJ', line=dict(color='#F39C12', width=3),
                text=df_daily_basic['Cum_PPJ'].apply(lambda x: f"<b>{x:,.0f}</b>" if x > 0 else ""), 
                textposition='top right', textfont=dict(size=12, color='#935116')
            ))
            
            fig_ppj.update_layout(title="일별 PPJ 및 누적 평균 PPJ", margin=dict(l=20, r=20, t=40, b=20), height=400, hovermode="x unified")
            fig_ppj.update_xaxes(type='category')
            
            # ★ 천장 여유 공간 확보 (최고수치의 1.2배) & 눈금 2500 고정
            max_ppj = max(df_daily_basic['PPJ'].max(), df_daily_basic['Cum_PPJ'].max())
            fig_ppj.update_yaxes(dtick=2500, tickformat=",", range=[0, max_ppj * 1.2 if max_ppj > 0 else 10])
            
            st.plotly_chart(fig_ppj, use_container_width=True)

        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # ==========================================
        # 4. 하단: 정밀 분석 추이 (MTBA / MTTR / MTBI)
        # ==========================================
        st.markdown(f"#### 📈 {selected_month} 정밀 분석 추이 (MTBA / MTTR / MTBI)")
        
        df_daily_mt = df_month.groupby(df_month['Date'].dt.date)[['MTBA', 'MTTR', 'MTBI']].max().reset_index()
        df_daily_mt['DateStr'] = pd.to_datetime(df_daily_mt['Date']).dt.strftime('%m/%d')
        
        # 누적 평균 미리 계산
        for col in ['MTBA', 'MTTR', 'MTBI']:
            df_daily_mt[f'{col}_cum_avg'] = df_daily_mt[col].expanding().mean()
            
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

        metrics = [
            ('MTBA', '#AED6F1', '#2E86C1'), 
            ('MTTR', '#F5B7B1', '#E74C3C'), 
            ('MTBI', '#A9DFBF', '#27AE60')
        ]

        for col, bar_color, line_color in metrics:
            # 1. 일별 수치 막대 그래프 (★ 숫자를 outside로 빼내어 시원하게 표시)
            fig1.add_trace(go.Bar(
                x=df_daily_mt['DateStr'], y=df_daily_mt[col], 
                name=f'{col} (일별)', marker_color=bar_color,
                text=df_daily_mt[col].apply(lambda x: f"<b>{x:,.0f}</b>" if x > 0 else ""), 
                textposition='outside', textfont=dict(size=11, color='#2C3E50')
            ), secondary_y=False)
            
            # 2. 날짜별 누적 평균 수치 꺾은선 (★ 숫자를 top right로 배치하여 막대 수치와 겹침 방지)
            fig1.add_trace(go.Scatter(
                x=df_daily_mt['DateStr'], y=df_daily_mt[f'{col}_cum_avg'], 
                mode='lines+markers+text', name=f'{col} 누적평균', 
                line=dict(color=line_color, width=2),
                text=df_daily_mt[f'{col}_cum_avg'].apply(lambda x: f"<b>{x:,.1f}</b>" if x > 0 else ""), 
                textposition='top right', textfont=dict(size=12, color=line_color)
            ), secondary_y=True)
        
        fig1.update_layout(
            height=500, 
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",
            barmode='group', 
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        fig1.update_xaxes(type='category')
        
        # ★ 천장 여유 공간 확보 (막대와 선 모두 최고치의 1.2배 확장)
        max_mt_daily = df_daily_mt[['MTBA', 'MTTR', 'MTBI']].max().max()
        max_mt_cum = df_daily_mt[['MTBA_cum_avg', 'MTTR_cum_avg', 'MTBI_cum_avg']].max().max()
        fig1.update_yaxes(title_text="일별 측정 수치", secondary_y=False, range=[0, max_mt_daily * 1.2 if max_mt_daily > 0 else 10])
        fig1.update_yaxes(title_text="누적 평균 수치", secondary_y=True, showgrid=False, range=[0, max_mt_cum * 1.2 if max_mt_cum > 0 else 10])
        
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 에러 발생 모듈(파이) & 분류별 발생 건수(가로바)
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### 🍩 에러 발생 모듈 (Err.Point) 점유율")
            err_point_counts = df_month.groupby('Err.Point')['Errorcount'].sum().reset_index()
            err_point_counts = err_point_counts[(err_point_counts['Err.Point'] != "") & (err_point_counts['Errorcount'] > 0)]
            
            if not err_point_counts.empty:
                fig2 = go.Figure(data=[go.Pie(labels=err_point_counts['Err.Point'], values=err_point_counts['Errorcount'], hole=.4)])
                
                fig2.update_traces(textfont_size=16)
                fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, legend=dict(font=dict(size=14)))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("해당 월에 Err.Point 데이터가 없습니다.")

        with col_g2:
            st.markdown("#### 📊 장애 분류별 발생 건수")
            type_counts = df_month.groupby('분류')['Errorcount'].sum().reset_index()
            type_counts = type_counts[(type_counts['분류'] != "") & (type_counts['Errorcount'] > 0)].sort_values(by='Errorcount', ascending=True)
            
            if not type_counts.empty:
                fig3 = go.Figure(data=[go.Bar(
                    y=type_counts['분류'], 
                    x=type_counts['Errorcount'], 
                    orientation='h', 
                    marker_color='#F39C12',
                    text=type_counts['Errorcount'].apply(lambda x: f"<b>{x:,.0f}</b>"), 
                    textposition='outside', # 가로막대도 글씨를 밖으로 빼서 선명하게!
                    textfont=dict(size=14, color='black')
                )])
                # X축 범위를 1.2배 늘려 글자가 짤리지 않게 보호
                max_type = type_counts['Errorcount'].max()
                fig3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="발생 건수", yaxis=dict(tickfont=dict(size=13)))
                fig3.update_xaxes(range=[0, max_type * 1.2 if max_type > 0 else 10])
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("해당 월에 분류 데이터가 없습니다.")
