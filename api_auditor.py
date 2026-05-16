from fastapi import FastAPI, File, UploadFile, HTTPException
import uvicorn
import shutil
import os
from datetime import datetime

# Importamos la clase que ya construiste y perfeccionaste en la Fase 1
from core_auditor import DocumentAuditor

# 1. Inicializamos la aplicación FastAPI
app = FastAPI(
    title="Industrial-Audit AI API",
    description="Enterprise-grade B2B API to digitize, read, and audit industrial documents using OCR.",
    version="1.0.0"
)

# 2. Rutas fijas de tus motores locales
POPPLER_PATH = r"C:\poppler\Library\bin"
TESSERACT_PATH = r"C:\Users\sombi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Inicializamos nuestro auditor base
auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)

# Carpeta temporal para guardar los archivos que suban los clientes por la web
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# 3. Endpoint de prueba (Para verificar que la API está viva)
@app.get("/", tags=["Health Check"])
def read_root():
    return {
        "status": "online",
        "message": "Industrial-Audit AI API is running smoothly.",
        "timestamp": datetime.now().isoformat()
    }

# 4. Endpoint principal: Aquí es donde los clientes enviarán sus PDFs
@app.post("/api/v1/audit", tags=["Auditor Core"])
async def audit_document(file: UploadFile = File(...)):
    # Verificación de seguridad básica: Asegurar que sea un PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")
    
    # Creamos una ruta temporal para guardar el archivo recibido
    temp_file_path = os.path.join(TEMP_DIR, file.filename)
    
    try:
        # Guardamos el archivo binario que viene de internet en nuestro disco duro
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ejecutamos la magia que programaste en la Fase 1
        raw_text = auditor.read_pdf(temp_file_path)
        
        if "Critical error" in raw_text:
            raise Exception(raw_text)
            
        serial_numbers = auditor.extract_data(raw_text)
        
        # 5. Estructuramos la respuesta en formato JSON profesional
        return {
            "filename": file.filename,
            "status": "SUCCESS" if serial_numbers else "WARNING",
            "extracted_data": {
                "serial_numbers_found": len(serial_numbers),
                "serials": serial_numbers
            },
            "audit_metadata": {
                "processed_at": datetime.now().isoformat(),
                "engine": "Tesseract OCR v5.5",
                "compliance_check": "PASSED" if serial_numbers else "FAILED"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error processing document: {str(e)}")
        
    finally:
        # Regla de oro de ciberseguridad: Borramos el archivo temporal del cliente 
        # inmediatamente después de procesarlo para no almacenar datos confidenciales.
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

# Punto de arranque para ejecutar con Python directamente
if __name__ == "__main__":
    uvicorn.run("api_auditor:app", host="127.0.0.1", port=8000, reload=True)