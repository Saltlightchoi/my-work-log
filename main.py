from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import DataManager

app = FastAPI(title="CS 장비관리 통합 시스템 API 서버", version="1.0.0")

# CORS 설정 (모바일 앱 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SPREADSHEET_ID = "1XcqwD79ggyoZ82OWVGRqJ_vXbA3fBU77b1vompB3bjA"

# ==========================================
# 📝 1. 업무일지 API
# ==========================================
class WorkLogEntry(BaseModel):
    날짜: str
    장비: str
    작성자: str
    업무내용: str
    비고: str = ""
    첨부: str = ""

@app.get("/api/worklog")
def get_work_log():
    """모바일 앱에서 업무일지 목록을 요청할 때 사용"""
    try:
        # 텍스트 컬럼 지정 방식도 대표님 원본대로 완벽하게 유지!
        db = DataManager(SPREADSHEET_ID, "업무일지", ["날짜", "장비", "작성자", "업무내용", "비고", "첨부"])
        df, _ = db.load()
        
        # DataFrame을 모바일이 읽을 수 있는 JSON 형태로 변환
        data = df.to_dict(orient="records")
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/worklog")
def add_work_log(entry: WorkLogEntry):
    """모바일 앱에서 새로운 업무일지를 등록할 때 사용"""
    try:
        db = DataManager(SPREADSHEET_ID, "업무일지")
        db.save_new_row(entry.dict())
        return {"status": "success", "message": "업무일지가 성공적으로 등록되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 🚨 2. Jam & 트러블슈팅 API
# ==========================================
class JamLogEntry(BaseModel):
    Date: str
    Totalunit: str
    Errorcode: str
    Errorcount: int
    Error_Masage: str  
    현상: str = ""
    원인: str = ""
    조치: str = ""
    Err_Point: str = ""
    분류: str = ""
    조치자: str = ""
    Err_Time: str = ""
    MTBA: str = ""
    MTTR: str = ""
    MTBI: str = ""
    도번: str = ""
    수량: str = ""
    입고일: str = ""
    반입일: str = ""
    조치위치: str = ""
    조치결과: str = ""

@app.get("/api/jamlog/{equipment_name}")
def get_jam_log(equipment_name: str):
    """모바일 앱에서 특정 장비의 Jam 이력을 요청할 때 사용"""
    try:
        exact_columns = [
            "Date", "Totalunit", "Errorcode", "Errorcount", "Error Masage", 
            "현상", "원인", "조치", "Err.Point", "분류", "조치자", "Err. Time", 
            "MTBA", "MTTR", "MTBI", "도번", "수량", "입고일", "반입일", "조치위치", "조치결과"
        ]
        db = DataManager(SPREADSHEET_ID, equipment_name, exact_columns)
        df, _ = db.load()
        
        data = df.to_dict(orient="records")
        return {"status": "success", "equipment": equipment_name, "data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"장비 데이터를 불러오는데 실패했습니다: {e}")

@app.post("/api/jamlog/{equipment_name}")
def add_jam_log(equipment_name: str, entry: JamLogEntry):
    """모바일 앱에서 특정 장비에 새로운 Jam 이력을 등록할 때 사용"""
    try:
        db = DataManager(SPREADSHEET_ID, equipment_name)
        
        # Pydantic 모델의 언더바(_) 변수를 구글시트 실제 컬럼명(공백, 점 등)에 맞춰 복구
        save_data = entry.dict()
        save_data["Error Masage"] = save_data.pop("Error_Masage")
        save_data["Err.Point"] = save_data.pop("Err_Point")
        save_data["Err. Time"] = save_data.pop("Err_Time")

        db.save_new_row(save_data)
        return {"status": "success", "message": f"{equipment_name} 장비에 Jam 이력이 등록되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
