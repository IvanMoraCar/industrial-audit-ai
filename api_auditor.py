from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import APIKeyHeader
import uvicorn
import shutil
import os
from datetime import datetime

from core_auditor import DocumentAuditor

app = FastAPI(
    title="Industrial-Audit AI API",
    description="Enterprise-grade B2B API to digitize, read, and audit industrial documents using OCR.",
    version="1.1.0"
)

# Hybrid path detection: Use system paths for Linux Cloud, and fallback to C:\ for local Windows
POPPLER_PATH = r"C:\poppler\Library\bin" if os.name != 'posix' else None
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe" if os.name != 'posix' else 'tesseract'

auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

VALID_API_KEYS = {
    "client-alpha-us-9982": "Premium Client - USA Corp",
    "client-beta-mx-4410": "Standard Client - Mexico Factory",
    "ivan-mora-dev-test": "Developer Admin Key"
}

def get_api_key(api_key: str = Depends(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is missing.")
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API Key. Access denied.")
    return VALID_API_KEYS[api_key]

@app.get("/", tags=["Health Check"])
def read_root(client_name: str = Depends(get_api_key)):
    return {
        "status": "online",
        "authorized_client": client_name,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/audit", tags=["Auditor Core"])
async def audit_document(file: UploadFile = File(...), client_name: str = Depends(get_api_key)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    
    temp_file_path = os.path.join(TEMP_DIR, file.filename)
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        raw_text = auditor.read_pdf(temp_file_path)
        if "Critical error" in raw_text:
            raise Exception(raw_text)
            
        serial_numbers = auditor.extract_data(raw_text)
        return {
            "filename": file.filename,
            "status": "SUCCESS" if len(serial_numbers) > 0 else "WARNING",
            "extracted_data": {
                "serial_numbers_found": len(serial_numbers),
                "serials": serial_numbers
            },
            "audit_metadata": {
                "processed_by_client": client_name,
                "processed_at": datetime.now().isoformat(),
                "engine": "Tesseract OCR v5.5",
                "compliance_check": "PASSED" if len(serial_numbers) > 0 else "FAILED"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    # Port configuration dynamically bound by Cloud environments or default local 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api_auditor:app", host="0.0.0.0", port=port, reload=True if os.name != 'posix' else False)