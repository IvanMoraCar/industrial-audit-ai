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
        # Connect Python with the local engine binaries
        self.poppler_path = poppler_path
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Regular expression pattern to match "SN-" followed by exactly 8 digits
        self.serial_pattern = r'\bSN-\d{8}\b'

    def read_pdf(self, pdf_path):
        """Converts the PDF to 300 DPI images and extracts raw text using OCR."""
        try:
            # Convert PDF pages to high-quality images
            images = convert_from_path(pdf_path, dpi=300, poppler_path=self.poppler_path)
            full_text = ""
            
            # Scan each page with Tesseract
            for img in images:
                # Page Segmentation Mode 6 is optimized for uniform text blocks
                text = pytesseract.image_to_string(img, config='--psm 6')
                full_text += text + "\n"
                
            return full_text
        except Exception as e:
            return f"Critical error: {e}"

    def extract_data(self, raw_text):
        """Applies the regular expression pattern to locate serial numbers."""
        return re.findall(self.serial_pattern, raw_text)

    def process_batch(self, input_dir, output_csv):
        """Processes all PDFs within a target directory and exports the dataset to CSV."""
        search_pattern = os.path.join(input_dir, '*.pdf')
        pdf_files = glob.glob(search_pattern)
        
        if not pdf_files:
            print(f"[WARNING] No PDF files found in '{input_dir}'")
            return

        print(f"-> Found {len(pdf_files)} documents to process. Starting batch job...\n")
        results_data = []
        
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            print(f"Processing: {filename}...")
            
            raw_text = self.read_pdf(pdf_path)
            
            if "Critical error" in raw_text:
                results_data.append([filename, "ERROR", "Could not read document"])
                continue
                
            serials = self.extract_data(raw_text)
            
            if len(serials) > 0:
                # Join multiple serial numbers with a semicolon if found in a single document
                serials_str = "; ".join(serials)
                results_data.append([filename, "SUCCESS", serials_str])
            else:
                results_data.append([filename, "WARNING", "No serial numbers detected"])
                
        self._export_to_csv(output_csv, results_data)

    def _export_to_csv(self, output_path, data):
        """Writes the structured multidimensional array into a CSV file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write structured headers
            writer.writerow(["Document Name", "Status", "Extracted Serial Numbers"])
            writer.writerows(data)
            
        print(f"\n[SUCCESS] Batch processing complete! Report saved to: {output_path}")


# ==========================================
# LOCAL EXECUTION ZONE
# ==========================================
if __name__ == "__main__":
    # Default system production paths
    POPPLER_PATH = r"C:\poppler\Library\bin" 
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    auditor = DocumentAuditor(POPPLER_PATH, TESSERACT_PATH)
    
    INPUT_DIR = "input_docs"
    OUTPUT_DIR = "output_docs"
    
    os.makedirs(INPUT_DIR, exist_ok=True)
    
    # Generate dynamic timestamped report filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = os.path.join(OUTPUT_DIR, f"audit_report_{timestamp}.csv")
    
    print("="*50)
    print("     INDUSTRIAL-AUDIT AI: BATCH PROCESSOR")
    print("="*50)
    auditor.process_batch(INPUT_DIR, report_name)