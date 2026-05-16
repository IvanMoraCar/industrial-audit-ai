import pytesseract
from pdf2image import convert_from_path
import re
import os

class AuditorDocumentos:
    """
    Clase encargada de digitalizar, leer y extraer datos críticos 
    de documentos técnicos o facturas.
    """
    def __init__(self, ruta_poppler, ruta_tesseract):
        # 1. Conectamos Python con los motores de tu computadora
        self.ruta_poppler = ruta_poppler
        pytesseract.pytesseract.tesseract_cmd = ruta_tesseract
        
        # 2. Definimos la regla: Buscar la palabra "SN-" seguida exactamente de 8 números
        self.patron_serie = r'\bSN-\d{8}\b'

    def leer_pdf(self, ruta_pdf):
        """Convierte el PDF a imágenes de 300 DPI y extrae el texto."""
        print(f"-> Abriendo y procesando: {ruta_pdf}")
        try:
            # Convertimos el PDF a imágenes de alta calidad (300 DPI)
            imagenes = convert_from_path(ruta_pdf, dpi=300, poppler_path=self.ruta_poppler)
            texto_completo = ""
            
            # Leemos cada página con la IA de Tesseract
            for i, img in enumerate(imagenes):
                print(f"-> Escaneando página {i + 1} con Tesseract OCR...")
                # psm 6 es ideal para bloques de texto uniformes
                texto = pytesseract.image_to_string(img, config='--psm 6')
                texto_completo += texto + "\n"
                
            return texto_completo
        except Exception as e:
            return f"Error crítico al leer el PDF: {e}"

    def extraer_datos(self, texto_crudo):
        """Aplica la expresión regular para encontrar el número de serie."""
        # Buscamos el patrón exacto en la sopa de letras extraída
        coincidencias = re.findall(self.patron_serie, texto_crudo)
        return coincidencias

# ==========================================
# ZONA DE EJECUCIÓN (Punto de entrada)
# ==========================================
if __name__ == "__main__":
    # 1. Tus rutas exactas de instalación (Intocables)
    RUTA_POPPLER = r"C:\poppler\Library\bin" 
    RUTA_TESSERACT = r"C:\Users\sombi\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    
    # 2. Encendemos el auditor
    mi_auditor = AuditorDocumentos(RUTA_POPPLER, RUTA_TESSERACT)
    print("¡Auditor IA inicializado! Analizando documento...\n")
    
    # 3. Le pasamos el PDF de prueba (Asegúrate de que exista en la misma carpeta)
    archivo_objetivo = "prueba.pdf"
    
    if os.path.exists(archivo_objetivo):
        texto_extraido = mi_auditor.leer_pdf(archivo_objetivo)
        
        # 4. Buscamos los datos críticos
        resultados = mi_auditor.extraer_datos(texto_extraido)
        
        # 5. Mostramos el reporte final
        print("\n" + "="*50)
        print("              RESULTADO DE LA AUDITORÍA")
        print("="*50)
        if resultados:
            print(f"[ÉXITO] Se detectaron {len(resultados)} números de serie válidos:")
            for serie in resultados:
                print(f"  -> {serie}")
        else:
            print("[ALERTA] No se encontraron números de serie válidos.")
        print("="*50)
    else:
        print(f"[ERROR] No se encontró el archivo '{archivo_objetivo}' en la carpeta actual.")