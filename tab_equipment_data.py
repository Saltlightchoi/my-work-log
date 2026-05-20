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

    def _render_navigation(self):
        """다른 탭으로 이동하기 위한 하단 드롭다운 내비게이션"""
        st.markdown("---")
        
        # main.py에 정의된 메뉴 목록과 정확히 일치해야 함
        menu_options = [
            "📝 팀 업무일지 대시보드",
            "✅ 장비 제작 Flow 전체 현황판",
            "📊 장비가동데이터",
            "🛠️ ECN & STN (장비 파트 및 수정사항 관리)"
        ]
        
        # 현재 세션에 저장된 메뉴를 가져오고, 인덱스를 찾음
        current_menu = st.session_state.get('current_menu', "📊 장비가동데이터")
        
        try:
            current_index = menu_options.index(current_menu)
        except ValueError:
            current_index = 2 # 기본값을 '장비가동데이터'로 설정
            
        # 드롭다운 위젯 생성 (고유 키 부여)
        selected_menu = st.selectbox(
            "🔗 다른 업무 탭으로 빠른 이동", 
            options=menu_options, 
            index=current_index,
            key="nav_EquipmentDataTab_dropdown" 
        )
        
        # 사용자가 다른 메뉴를 선택하면 상태 업데이트 및 화면 새로고침
        if selected_menu != current_menu:
            st.session_state['current_menu'] = selected_menu
            st.rerun()

    def render(self):
        # 1. 탭 헤더
        st.header("📊 장비가동데이터")
        
        # ---------------------------------------------------------
        # 2. 데이터 시각화 및 분석 로직 
        # (기존에 작성하셨던 깃허브 데이터 불러오기 및 Plotly 차트 생성 코드를 이 아래에 위치시키면 됩니다.)
        # ---------------------------------------------------------
        st.info("이곳에 기존에 작성하셨던 장비 가동 데이터 분석 및 시각화 코드가 들어갑니다.")
        
        
        # ---------------------------------------------------------
        # 3. 하단 메뉴 이동 내비게이션 렌더링
        # ---------------------------------------------------------
        self._render_navigation()
