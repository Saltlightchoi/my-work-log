import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. 페이지 기본 설정 (가장 위에 위치해야 합니다)
# ==========================================
st.set_page_config(
    page_title="통합 업무 및 설비 관리 시스템", 
    layout="wide", # 화면을 넓게 사용
    initial_sidebar_state="expanded"
)

st.title("통합 업무 및 설비 관리 시스템")

# ==========================================
# 2. 상단 탭(Tab) 생성
# ==========================================
# 3개의 탭을 생성합니다. 클릭할 때마다 해당 영역으로 부드럽게 전환됩니다.
tab1, tab2, tab3 = st.tabs(["📝 업무일지", "✅ CS 작업체크시트", "📊 장비가동데이터"])

# ==========================================
# 3. 탭 1: 업무일지 영역
# ==========================================
with tab1:
    st.header("📝 업무일지")
    st.info("이곳에 기존에 작성하시던 업무일지 관련 코드를 넣어주세요.")
    
    # 예시 UI
    log_date = st.date_input("날짜 선택")
    log_content = st.text_area("금일 업무 내용 작성", height=150)
    if st.button("업무일지 저장", key="btn_worklog"):
        st.success("업무일지가 저장되었습니다.")

# ==========================================
# 4. 탭 2: CS 작업체크시트 영역
# ==========================================
with tab2:
    st.header("✅ CS 작업체크시트")
    st.info("이곳에 CS 작업체크시트 관련 코드를 넣어주세요.")
    
    # 예시 UI
    st.subheader("일일 점검 항목")
    col_a, col_b = st.columns(2)
    with col_a:
        st.checkbox("메인 파워 정상 확인")
        st.checkbox("메인 Air 압력 정상 확인")
        st.checkbox("EMO 버튼 해제 상태 확인")
    with col_b:
        st.checkbox("Fan 센서 작동 확인")
        st.checkbox("안전 커버 닫힘 확인")
        
    if st.button("체크시트 제출", key="btn_cs"):
        st.success("점검 내역이 제출되었습니다.")

# ==========================================
# 5. 탭 3: 장비가동데이터 영역
# ==========================================
with tab3:
    st.header("📊 장비가동데이터")
    
    # 5-1. 장비 및 호기 선택 (좌우 나란히 배치)
    col1, col2 = st.columns(2)
    with col1:
        equipment = st.selectbox("장비 선택", ["SLH1", "4010H", "기타 장비"])
    with col2:
        unit = st.selectbox("호기 선택", ["1호기", "2호기", "3호기", "4호기", "5호기"])
        
    st.divider() # 화면을 분리하는 가로선
    
    # 5-2. 데이터 불러오기 
    # (실제 엑셀 파일을 연동할 때는 아래 코드를 사용하세요)
    # try:
    #     df = pd.read_csv("SLH1(WOOIK) Daily Test Report_26년.xlsx - 26'03.csv")
    # except:
    #     st.error("데이터 파일을 찾을 수 없습니다.")
    
    # 테스트를 위한 예시 데이터프레임 (첨부해주신 양식 참고)
    data = {
        '날짜': [f"3월 {i}일" for i in range(1, 16)],
        '생산량(Output)': [3712, 6221, 5879, 9037, 2220, 0, 0, 7425, 8000, 8500, 7800, 8100, 8900, 0, 0],
        'Jam_Count': [3, 2, 3, 4, 2, 0, 0, 1, 5, 2, 3, 2, 4, 0, 0]
    }
    df = pd.DataFrame(data)
    
    st.subheader(f"{equipment} - {unit} 가동 현황")
    
    # 5-3. 이중 축 그래프 그리기 (Plotly)
    fig = go.Figure()

    # (1) 생산량 - 막대 그래프 (파란색)
    fig.add_trace(go.Bar(
        x=df['날짜'], 
        y=df['생산량(Output)'], 
        name='생산량(Output)', 
        marker_color='#5B9BD5', 
        yaxis='y1'
    ))

    # (2) Jam 발생 건수 - 꺾은선 그래프 (주황색)
    fig.add_trace(go.Scatter(
        x=df['날짜'], 
        y=df['Jam_Count'], 
        name='Jam 건수', 
        mode='lines+markers',
        line=dict(color='#ED7D31', width=3), 
        marker=dict(size=8),
        yaxis='y2' # 두 번째 Y축 사용
    ))

    # (3) 그래프 레이아웃 및 이중 축 설정
    fig.update_layout(
        title_text="일별 생산량 및 Jam 발생 추이",
        height=500,
        xaxis=dict(title="날짜"),
        yaxis=dict(
            title="생산량 (EA)",
            titlefont=dict(color="#5B9BD5"),
            tickfont=dict(color="#5B9BD5"),
            side="left"
        ),
        yaxis2=dict(
            title="Jam 발생 (건)",
            titlefont=dict(color="#ED7D31"),
            tickfont=dict(color="#ED7D31"),
            overlaying="y", # 첫 번째 Y축 위에 겹침
            side="right",   # 오른쪽에 표시
            range=[0, max(df['Jam_Count']) + 5] # 그래프가 위쪽으로 몰리지 않게 여백 추가
        ),
        legend=dict(
            orientation="h", # 범례를 가로로 배치
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified" # 마우스를 올렸을 때 두 데이터의 값이 한 번에 보이도록 설정
    )

    # 완성된 그래프를 스트림릿 화면에 출력
    st.plotly_chart(fig, use_container_width=True)
