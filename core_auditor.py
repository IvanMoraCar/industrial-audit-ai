import pytesseract
from pdf2image import convert_from_path
import re
import os
import glob
import csv
from datetime import datetime

class DocumentAuditor:
    """
    Class responsible for digitizing, reading, and extracting critical data 
    from technical documents or invoices.
    """
    def __init__(self, poppler_path, tesseract_path):
        self.poppler_path = poppler_path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.serial_pattern = r'\bSN-\d{8}\b'

    def read_pdf(self, pdf_path):
        """Converts the PDF to 300 DPI images and extracts text."""
        try:
            images = convert_from_path(pdf_path, dpi=300, poppler_path=self.poppler_path)
            full_text = ""
            for img in images:
                text = pytesseract.image_to_string(img, config='--psm 6')
                full_text += text + "\n"
            return full_text
        except Exception as e:
            return f"Critical error: {e}"

    def extract_data(self, raw_text):
        """Applies the regular expression to find the serial number."""
        return re.findall(self.serial_pattern, raw_text)

    def process_batch(self, input_dir, output_csv):
        """Processes all PDFs in a directory and exports results to CSV."""
        # 1. Use glob to find all PDFs in the input folder
        search_pattern = os.path.join(input_dir, '*.pdf')
        pdf_files = glob.glob(search_pattern)
        
        if not pdf_files:
            print(f"[WARNING] No PDF files found in '{input_dir}'")
            return

        print(f"-> Found {len(pdf_files)} documents to process. Starting batch job...\n")
        
        # Array to hold the data for the CSV
        results_data = []
        
        # 2. Iterate through each PDF
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path) # Gets just the file name, not the whole path
            print(f"Processing: {filename}...")
            
            raw_text = self.read_pdf(pdf_path)
            
            if "Critical error" in raw_text:
                results_data.append([filename, "ERROR", "Could not read document"])
                continue
                
            serials = self.extract_data(raw_text)
            
            # 3. Format the data for the report
            if serials:
                # If it finds multiple serials in one doc, join them with a semicolon
                serials_str = "; ".join(serials)
                results_data.append([filename, "SUCCESS", serials_str])
            else:
                results_data.append([filename, "WARNING", "No serial numbers detected"])
                
        # 4. Export to CSV
        self._export_to_csv(output_csv, results_data)

    def _export_to_csv(self, output_path, data):
        """Writes the structured data to a CSV file."""
        # Ensure the output directory exists before saving
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Open file in write mode ('w')
        with open(output_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow(["Document Name", "Status", "Extracted Serial Numbers"])
            # Write all the data rows
            writer.writerows(data)
            
        print(f"\n[SUCCESS] Batch processing complete! Report saved to: {output_path}")

# ==========================================
# EXECUTION ZONE
# ==========================================
if __name__ == "__main__":
    POPPLER_PATH = r"C:\poppler\Library\bin" 
    TESSERACT_PATH = r"C:\Users\sombi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    
    auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)
    
    # Directories
    INPUT_DIR = "input_docs"
    OUTPUT_DIR = "output_reports"
    
    # Create the input directory automatically if the user forgot
    os.makedirs(INPUT_DIR, exist_ok=True)
    
    # Generate a dynamic report name with current date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = os.path.join(OUTPUT_DIR, f"audit_report_{timestamp}.csv")
    
    print("="*50)
    print("     INDUSTRIAL-AUDIT AI: BATCH PROCESSOR")
    print("="*50)
    auditor.process_batch(INPUT_DIR, report_name)