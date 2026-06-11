import streamlit as st
import pandas as pd
from datetime import datetime
from config import DataManager

class JamLogTab:
    def __init__(self, db_jam):
        self.db_jam = db_jam

    def render(self):
        # ==========================================
        # ★ Session State 초기화 (자동완성을 위한 메모리 생성)
        # ==========================================
        if "err_code" not in st.session_state: st.session_state.err_code = ""
        if "err_point" not in st.session_state: st.session_state.err_point = ""
        if "err_msg" not in st.session_state: st.session_state.err_msg = ""

        # ==========================================
        # ★ 핵심 로직: 3개 중 1개만 입력해도 나머지를 찾아주는 자동완성 함수
        # ==========================================
        def autofill(source_field):
            # 현재 선택된 장비 확인 (장비에 맞는 에러리스트를 부르기 위함)
            equip_name = st.session_state.get("equip_val", "SLH1 #1")
            target_error_tab = "SLH1_Rdimm_ErrorList" if "#1" in equip_name else "SLH1_Socamm_ErrorList"
            
            try:
                db_err = DataManager(self.db_jam.spreadsheet_id, target_error_tab)
                df_err, _ = db_err.load()
                if not df_err.empty:
                    df_err.columns = df_err.columns.astype(str).str.strip()
            except Exception:
                return # 에러 시트가 없으면 조용히 종료
            
            # 사용자가 방금 입력한 값 가져오기
            search_val = str(st.session_state[source_field]).strip()
            if not search_val or df_err.empty: return
            
            # 파이썬 변수명과 구글 시트의 헤더 매핑
            col_map = {"err_code": "알람코드", "err_point": "모듈", "err_msg": "알람명"}
            search_col = col_map.get(source_field)
            
            if search_col in df_err.columns:
                # 1단계: 완전히 똑같은 글자가 있는지 검색
                match = df_err[df_err[search_col].astype(str).str.strip() == search_val]
                
                # 2단계: 똑같은 게 없으면 그 단어가 '포함'된 항목 검색
                if match.empty:
                    match = df_err[df_err[search_col].astype(str).str.contains(search_val, case=False, na=False)]
                    
                # 찾았으면 나머지 빈칸들에 데이터 강제 주입!
                if not match.empty:
                    row = match.iloc[0]
                    if source_field != "err_code" and "알람코드" in df_err.columns:
                        st.session_state.err_code = str(row["알람코드"])
                    if source_field != "err_point" and "모듈" in df_err.columns:
                        st.session_state.err_point = str(row["모듈"])
                    if source_field != "err_msg" and "알람명" in df_err.columns:
                        st.session_state.err_msg = str(row["알람명"])

        # ==========================================
        # 장비명 세팅 및 심플 CSS
        # ==========================================
        DB_SHEET_OPTIONS = ["SLH1 #1", "SLH1 #4"]

        st.markdown("""
            <style>
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            div[data-testid="stWidgetLabel"] p { font-size: 14px !important; font-weight: 600 !important; color: #222 !important; }
            div[data-testid="stTextInput"] input, 
            div[data-testid="stDateInput"] input, 
            div[data-testid="stTimeInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span { font-size: 14px !important; }
            </style>
        """, unsafe_allow_html=True)

        # 상단 네비게이션 & 우측 액션 버튼
        menu_options = [
            "📝 팀 업무일지 대시보드", "✅ 장비 제작 Flow 전체 현황판", 
            "📊 장비가동데이터", "🛠️ ECN & STN (장비 파트 및 수정사항 관리)", "🚨 Jam & 트러블슈팅 이력"
        ]
        
        nav_cols = st.columns([6, 1, 1, 1])
        with nav_cols[0]:
            selected_menu = st.selectbox("메뉴", menu_options, index=menu_options.index(st.session_state.get('current_menu', "🚨 Jam & 트러블슈팅 이력")), key="menu_jam_log", label_visibility="collapsed")
            if selected_menu != st.session_state.get('current_menu'):
                st.session_state['current_menu'] = selected_menu; st.rerun()
                
        with nav_cols[1]: btn_write = st.button("📝 저장", use_container_width=True)
        with nav_cols[2]: btn_edit = st.button("✏️ 수정", use_container_width=True)
        with nav_cols[3]: btn_del = st.button("🗑️ 삭제", use_container_width=True)

        st.markdown("---")

        # ==========================================
        # 입력 폼 (자동완성 콜백 연결)
        # ==========================================
        with st.container(border=True):
            # ▶ 1줄: 장비명(key 지정), ErrorCode(콜백 연결)
            r1 = st.columns([1.8, 1.2, 1.0, 1.2, 1.2, 0.8])
            with r1[0]: equip_val = st.selectbox("장비명", DB_SHEET_OPTIONS, key="equip_val")
            with r1[1]: date_val = st.
