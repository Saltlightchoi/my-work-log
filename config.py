# config.py (변경 예시)
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

class DataManager:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        # 구글 API 인증 정보 로드
        creds = Credentials.from_service_account_file('credentials.json')
        self.client = gspread.authorize(creds)

    def load(self, sheet_name):
        # 엑셀 데이터 대신 구글 시트 데이터를 로드
        sh = self.client.open_by_key(self.spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        return pd.DataFrame(worksheet.get_all_records())

    def save(self, sheet_name, df):
        # 변경사항 저장
        sh = self.client.open_by_key(self.spreadsheet_id)
        worksheet = sh.worksheet(sheet_name)
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
