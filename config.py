import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets API 인증 설정
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'credentials.json'

class DataManager:
    def __init__(self, spreadsheet_id, sheet_name, text_columns=None):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name
        self.text_columns = text_columns or []
        
        # 인증 객체 생성
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        self.client = gspread.authorize(self.creds)
        
    def load(self):
        """구글 시트에서 데이터를 로드하여 DataFrame으로 반환"""
        try:
            sh = self.client.open_by_key(self.spreadsheet_id)
            worksheet = sh.worksheet(self.sheet_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            
            # 텍스트 컬럼 보정
            for col in self.text_columns:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            
            return df, None # 깃허브 SHA 방식은 사용하지 않으므로 None 반환
        except Exception as e:
            print(f"로드 오류: {e}")
            return pd.DataFrame(columns=self.text_columns), None

    def save(self, df, sha=None, message=None):
        """구글 시트에 데이터를 즉시 저장"""
        sh = self.client.open_by_key(self.spreadsheet_id)
        worksheet = sh.worksheet(self.sheet_name)
        
        # 시트 초기화 후 헤더와 함께 전체 데이터 업데이트
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
