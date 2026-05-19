# config.py 상단 수정
import pandas as pd
import streamlit as st
import gspread
# oauth2client 대신 oauth2client.service_account를 정확히 명시합니다.
from oauth2client.service_account import ServiceAccountCredentials 

# 그리고 아래처럼 CREDS_FILE 경로를 정확히 지정하세요.
import os
# 현재 파일(config.py)이 있는 위치를 기준으로 파일을 찾습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(BASE_DIR, 'service-account.json') # 파일 이름 확인!

# Google Sheets API 인증 범위
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service-account.json'

class DataManager:
    def __init__(self, spreadsheet_id, sheet_name, text_columns=None):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.text_columns = text_columns or []
        
        # 인증 및 시트 연결
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
        
@st.cache_data(ttl=600) # 10분(600초) 동안 데이터를 캐시함
    def load(self):
        data = self.sheet.get_all_records()
        df = pd.DataFrame(data)
        for col in self.text_columns:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df, None

    def save(self, df, sha=None, message=None):
        # 시트 초기화 후 전체 업데이트
        self.sheet.clear()
        self.sheet.update([df.columns.values.tolist()] + df.values.tolist())
