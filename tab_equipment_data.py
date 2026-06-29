import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import DataManager
from datetime import datetime

class EquipmentDataTab:
    def __init__(self, db_jam):
        # app.py로부터 db_jam(구글시트 객체)을 받습니다.
        self.db_jam = db_jam

    def render(self):
        st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📊 장비 가동 정밀 데이터 분석")
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
        
        # 장비 선택 폼
        DB_SHEET_OPTIONS = ["SLH1 #1", "SLH1 #4", "SLH1 #5", "SLH1 #6", "SLH1 #7"]
        
        col1, col2 = st.columns([2, 8])
        with col1:
            equip_val = st.selectbox("분석할 장비 선택", DB_SHEET_OPTIONS)

        # ==========================================
        # 1. Jam 데이터 로드
        # ==========================================
        if equip_val == "SLH1 #1": 
            target_tab = "SLH1 #1"
        else: 
            target_tab = equip_val
            
        exact_columns = [
            "Date", "Totalunit", "Errorcode", "Errorcount", "Error Masage", 
            "현상", "원인", "조치", "Err.Point", "분류", "조치자", "Err. Time", 
            "MTBA", "MTTR", "MTBI", "도번", "수량", "입고일", "반입일", "조치위치", "조치결과"
        ]
        
        try:
            db_machine = DataManager(self.db_jam.spreadsheet_id, target_tab, exact_columns)
            df, _ = db_machine.load()
        except Exception as e:
            st.error(f"🚨 데이터를 불러오지 못했습니다. 시트를 확인해주세요: {e}")
            return
            
        if df.empty:
            st.info(f"💡 '{equip_val}' 장비에 등록된 Jam 데이터가 없어 그래프를 그릴 수 없습니다.")
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
        # 3. 상단: 생산 Unit 대비 Jam 발생 & PPJ 그래프 (점선/이중축 적용)
        # ==========================================
        st.markdown(f"#### 📊 {selected_month} 기본 가동 현황 (PPJ 및 생산대비 Jam)")
        
        # 일별 데이터 집계
        df_daily_basic = df_month.groupby(df_month['Date'].dt.date).agg({
            'Totalunit': 'max',  # 일별 최대 생산량
            'Errorcount': 'sum'  # 일별 에러 건수 총합
        }).reset_index()

        # PPJ (Parts Per Jam) 계산: 생산량 / 에러건수 (에러가 0일 경우 생산량 전체를 PPJ로 간주)
        df_daily_basic['PPJ'] = df_daily_basic.apply(
            lambda row: row['Totalunit'] / row['Errorcount'] if row['Errorcount'] > 0 else row['Totalunit'], 
            axis=1
        )
        
        # 기간별(월별) 평균 PPJ 계산
        total_unit_month = df_daily_basic['Totalunit'].sum()
        total_error_month = df_daily_basic['Errorcount'].sum()
        period_ppj = total_unit_month / total_error_month if total_error_month > 0 else total_unit_month

        col_top1, col_top2 = st.columns(2)
        
        # [그래프 1] 생산 Unit 대비 Jam 발생 (이중 축 점선 그래프)
        with col_top1:
            fig_tu = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 생산량 (좌측 축, 실선+마커)
            fig_tu.add_trace(
                go.Scatter(x=df_daily_basic['Date'], y=df_daily_basic['Totalunit'], 
                           mode='lines+markers', name='생산량 (Total Unit)', line=dict(color='#3498DB', width=2)),
                secondary_y=False
            )
            # Jam 발생 (우측 축, 점선+마커)
            fig_tu.add_trace(
                go.Scatter(x=df_daily_basic['Date'], y=df_daily_basic['Errorcount'], 
                           mode='lines+markers', name='Jam 발생 (건)', line=dict(color='#E74C3C', width=2, dash='dot')),
                secondary_y=True
            )
            
            fig_tu.update_layout(title="생산 Unit 대비 Jam 발생 추이", margin=dict(l=20, r=20, t=40, b=20), height=350, hovermode="x unified")
            fig_tu.update_yaxes(title_text="생산량", secondary_y=False)
            fig_tu.update_yaxes(title_text="Jam 건수", secondary_y=True)
            st.plotly_chart(fig_tu, use_container_width=True)

        # [그래프 2] 일별 PPJ 및 기간별 PPJ
        with col_top2:
            fig_ppj = go.Figure()
            
            # 일별 PPJ (점선+마커)
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['Date'], y=df_daily_basic['PPJ'], 
                mode='lines+markers', name='일별 PPJ', line=dict(color='#27AE60', width=2)
            ))
            
            # 기간별 평균 PPJ (수평 점선)
            fig_ppj.add_trace(go.Scatter(
                x=df_daily_basic['Date'], y=[period_ppj] * len(df_daily_basic), 
                mode='lines', name=f'기간별 평균 PPJ ({int(period_ppj):,}개)', line=dict(color='#F39C12', width=2, dash='dash')
            ))
            
            fig_ppj.update_layout(title="일별 PPJ 및 기간별 평균 PPJ", margin=dict(l=20, r=20, t=40, b=20), height=350, hovermode="x unified")
            st.plotly_chart(fig_ppj, use_container_width=True)

        st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

        # ==========================================
        # 4. 하단: 정밀 분석 그래프 3개 (MTBA/MTTR/MTBI 및 분류)
        # ==========================================
        st.markdown(f"#### 📈 {selected_month} 정밀 분석 추이")
        
        # ✅ 변경점: MTBA, MTTR, MTBI를 평균(mean)이 아닌 그날 입력된 최대치(max) 수치 그대로 가져옵니다.
        df_daily_mt = df_month.groupby(df_month['Date'].dt.date)[['MTBA', 'MTTR', 'MTBI']].max().reset_index()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_daily_mt['Date'], y=df_daily_mt['MTBA'], mode='lines+markers', name='MTBA', line=dict(color='#2E86C1', width=3)))
        fig1.add_trace(go.Scatter(x=df_daily_mt['Date'], y=df_daily_mt['MTTR'], mode='lines+markers', name='MTTR', line=dict(color='#E74C3C', width=3)))
        fig1.add_trace(go.Scatter(x=df_daily_mt['Date'], y=df_daily_mt['MTBI'], mode='lines+markers', name='MTBI', line=dict(color='#27AE60', width=3)))
        
        fig1.update_layout(
            height=350, 
            margin=dict(l=20, r=20, t=30, b=20),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
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
                fig2.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350)
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
                    text=type_counts['Errorcount'], 
                    textposition='auto'
                )])
                fig3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=350, xaxis_title="발생 건수")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("해당 월에 분류 데이터가 없습니다.")
