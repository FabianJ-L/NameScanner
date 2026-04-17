import os
import shutil
import easyocr
from PIL import Image, ImageOps
import numpy as np
from thefuzz import process

# --- KONFIGURATION ---
SOURCE_DIRECTORY = "inbox"
TARGET_DIRECTORY = "sorted"
TARGET_AREA_COORDS = (200, 240, 900, 300) 

# --- DATENBANK ---
REFERENCE_ENTITIES = [
    "Janisch-Lang Fabian",
    "Häusler Valentin",
    "Müller Max",
    "Schmidt Sarah"
]

os.makedirs(TARGET_DIRECTORY, exist_ok=True)
ocr_engine = easyocr.Reader(["de", "en"], gpu=False)

def apply_image_enhancement(img_input: Image.Image) -> Image.Image:
    """Bereitet das Bild für die Texterkennung vor."""
    img_input = img_input.convert("RGB")
    red_channel, _, _ = img_input.split()
    enhanced_data = 255 - np.array(red_channel)
    result_img = Image.fromarray(enhanced_data)
    result_img = ImageOps.autocontrast(result_img, cutoff=5)
    return result_img

def sanitize_string(raw_text: str) -> str:
    """Entfernt ungültige Zeichen für Dateisysteme."""
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß- ")
    return "".join(char for char in raw_text if char in allowed_chars).strip()

def match_text_to_reference(ocr_output: list) -> str:
    """Vergleicht OCR-Ergebnis mit Referenzliste."""
    combined_text = " ".join(ocr_output).strip()
    
    if not combined_text:
        return "UNKNOWN_ENTITY"

    match, confidence = process.extractOne(combined_text, REFERENCE_ENTITIES)
    
    print(f"  OCR-Eingabe: '{combined_text}' -> Match: '{match}' (Sicherheit: {confidence}%)")
    
    if confidence > 60:
        return match.replace(" ", "_")
    
    return sanitize_string(combined_text).replace(" ", "_")

def process_single_file(file_path: str, area_coords: tuple) -> list:
    img = Image.open(file_path)
    roi = img.crop(area_coords)
    enhanced_roi = apply_image_enhancement(roi)
    enhanced_roi.save("debug_roi.png")
    
    return ocr_engine.readtext(
        np.array(enhanced_roi), 
        detail=0, 
        paragraph=True,
        allowlist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß- "
    )

def run_batch_process():
    supported_extensions = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    files_to_process = [f for f in os.listdir(SOURCE_DIRECTORY) 
                        if os.path.splitext(f)[1].lower() in supported_extensions]

    if not files_to_process:
        print("Keine Dateien gefunden.")
        return

    success_count, fail_count = 0, 0

    for filename in files_to_process:
        file_path = os.path.join(SOURCE_DIRECTORY, filename)
        ext = os.path.splitext(filename)[1].lower()
        
        try:
            print(f"\nBearbeite: {filename}...")
            ocr_results = process_single_file(file_path, TARGET_AREA_COORDS)
            
            final_identifier = match_text_to_reference(ocr_results)
            new_filename = f"{final_identifier}{ext}"
            new_path = os.path.join(TARGET_DIRECTORY, new_filename)
            
            # Konfliktlösung
            counter = 1
            while os.path.exists(new_path):
                base_name = os.path.splitext(new_filename)[0]
                new_path = os.path.join(TARGET_DIRECTORY, f"{base_name}_{counter}{ext}")
                counter += 1
            
            shutil.move(file_path, new_path)
            print(f"  ✓ Gespeichert als: {os.path.basename(new_path)}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Fehler bei {filename}: {e}")
            fail_count += 1

    print(f"\nAbgeschlossen! {success_count} erfolgreich, {fail_count} fehlerhaft.")

if __name__ == "__main__":
    run_batch_process()