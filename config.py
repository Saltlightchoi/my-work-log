import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets API 인증 범위
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json'

class DataManager:
    def __init__(self, spreadsheet_id, sheet_name, text_columns=None):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.text_columns = text_columns or []
        
        # 인증 및 시트 연결
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)

    def load(self):
        # 깃허브 SHA 방식 제거, 데이터 로드
        data = self.sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 텍스트 컬럼 보정
        for col in self.text_columns:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df, None # SHA 필요 없음

    def save(self, df, sha=None, message=None):
        # 시트 초기화 후 전체 업데이트
        self.sheet.clear()
        self.sheet.update([df.columns.values.tolist()] + df.values.tolist())
