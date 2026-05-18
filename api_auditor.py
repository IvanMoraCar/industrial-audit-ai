from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import APIKeyHeader
import uvicorn
import shutil
import os
from datetime import datetime

# Import the core logic engine class
from core_auditor import DocumentAuditor

# Initialize the application with professional OpenAPI metadata
app = FastAPI(
    title="Industrial-Audit AI API",
    description="Enterprise-grade B2B API to digitize, read, and audit industrial documents using OCR.",
    version="1.1.0"
)

# Standardized default paths for binary engines
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize global auditor instance
auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)

# Directory container for handling stream uploads safely
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# Define API Key location configuration inside HTTP Headers
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Simulated secure registry mapping active client credentials to subscriptions
VALID_API_KEYS = {
    "client-alpha-us-9982": "Premium Client - USA Corp",
    "client-beta-mx-4410": "Standard Client - Mexico Factory",
    "ivan-mora-dev-test": "Developer Admin Key"
}

def get_api_key(api_key: str = Depends(api_key_header)):
    """Gatekeeper function executing authorization checks via dependency injection."""
    if not api_key:
        raise HTTPException(
            status_code=401, 
            detail="API Key is missing. Please provide 'X-API-Key' in your request headers."
        )
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403, 
            detail="Invalid API Key. Access denied. Please verify your subscription status."
        )
    return VALID_API_KEYS[api_key]

# API Service Status Endpoint
@app.get("/", tags=["Health Check"])
def read_root(client_name: str = Depends(get_api_key)):
    return {
        "status": "online",
        "authorized_client": client_name,
        "timestamp": datetime.now().isoformat()
    }

# Secure Document Processing Upload Pipeline Endpoint
@app.post("/api/v1/audit", tags=["Auditor Core"])
async def audit_document(
    file: UploadFile = File(...), 
    client_name: str = Depends(get_api_key)
):
    # Enforce strict multi-part type validation filtering for PDF documents
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    
    temp_file_path = os.path.join(TEMP_DIR, file.filename)
    
    try:
        # Buffer incoming stream chunks into disk storage
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Invoke core OCR extraction subroutines
        raw_text = auditor.read_pdf(temp_file_path)
        
        if "Critical error" in raw_text:
            raise Exception(raw_text)
            
        serial_numbers = auditor.extract_data(raw_text)
        
        # Build clean JSON structures mapping data schema requirements
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error processing document: {str(e)}")
        
    finally:
        # Security Guardrail: Force complete deletion of temporary client files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Web Server Lifecycle Entry Point
if __name__ == "__main__":
    uvicorn.run("api_auditor:app", host="127.0.0.1", port=8000, reload=True)