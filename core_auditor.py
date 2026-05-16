import pytesseract
from pdf2image import convert_from_path
import re
import os

class DocumentAuditor:
    """
    Class responsible for digitizing, reading, and extracting critical data 
    from technical documents or invoices.
    """
    def __init__(self, poppler_path, tesseract_path):
        # 1. Connect Python with the local engines
        self.poppler_path = poppler_path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # 2. Define the rule: Look for "SN-" followed by exactly 8 digits
        self.serial_pattern = r'\bSN-\d{8}\b'

    def read_pdf(self, pdf_path):
        """Converts the PDF to 300 DPI images and extracts text."""
        print(f"-> Processing document: {pdf_path}")
        try:
            # Convert PDF to high-quality images (300 DPI)
            images = convert_from_path(pdf_path, dpi=300, poppler_path=self.poppler_path)
            full_text = ""
            
            # Read each page using Tesseract AI
            for i, img in enumerate(images):
                print(f"-> Scanning page {i + 1} with Tesseract OCR...")
                # psm 6 is ideal for uniform text blocks
                text = pytesseract.image_to_string(img, config='--psm 6')
                full_text += text + "\n"
                
            return full_text
        except Exception as e:
            return f"Critical error reading PDF: {e}"

    def extract_data(self, raw_text):
        """Applies the regular expression to find the serial number."""
        # Search for the exact pattern in the extracted text
        matches = re.findall(self.serial_pattern, raw_text)
        return matches

# ==========================================
# EXECUTION ZONE (Entry point)
# ==========================================
if __name__ == "__main__":
    # 1. Exact installation paths (Do not change)
    POPPLER_PATH = r"C:\poppler\Library\bin" 
    TESSERACT_PATH = r"C:\Users\sombi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    
    # 2. Initialize the auditor
    auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)
    print("AI Auditor successfully initialized! Analyzing document...\n")
    
    # 3. Target test PDF (Ensure it exists in the same folder)
    target_file = "test_report.pdf"
    
    if os.path.exists(target_file):
        extracted_text = auditor.read_pdf(target_file)
        # 4. Search for critical data
        results = auditor.extract_data(extracted_text)
        
        # 5. Display final report
        print("\n" + "="*50)
        print("                 AUDIT RESULT")
        print("="*50)
        if results:
            print(f"[SUCCESS] Detected {len(results)} valid serial numbers:")
            for serial in results:
                print(f"  -> {serial}")
        else:
            print("[WARNING] No valid serial numbers found in the document.")
        print("="*50)
    else:
        print(f"[ERROR] Target file '{target_file}' not found in the current directory.")