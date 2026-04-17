import os
import shutil
import easyocr
from PIL import Image, ImageOps
import numpy as np
from thefuzz import process  # Für die automatische Fehlerkorrektur

# --- KONFIGURATION ---
INPUT_FOLDER = "inbox"
OUTPUT_FOLDER = "sorted"
NAME_BOX = (200, 240, 900, 300)  # Deine optimierten Koordinaten

# --- DEINE SCHÜLERLISTE ---
# Hier alle Namen eintragen, die vorkommen können. 
# Das Skript korrigiert OCR-Fehler (wie 'FADIAN') automatisch auf diese Namen.
SCHUELER_DATENBANK = [
    "Janisch-Lang Fabian",
    "Häusler Valentin",
    "Müller Max",
    "Schmidt Sarah"
    # ... hier weitere Namen ergänzen
]

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
reader = easyocr.Reader(["de", "en"], gpu=False)

def preprocess_blue_ink(img: Image.Image) -> Image.Image:
    """Optimiert blaue Tinte auf weißem Hintergrund."""
    img = img.convert("RGB")
    r, _, _ = img.split()
    enhanced = 255 - np.array(r)
    result = Image.fromarray(enhanced)
    result = ImageOps.autocontrast(result, cutoff=5)
    return result

def clean_part(text: str) -> str:
    """Entfernt Sonderzeichen für saubere Dateinamen."""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß- ")
    return "".join(c for c in text if c in allowed).strip()

def get_best_name_match(ocr_results: list) -> str:
    """Vergleicht OCR-Text mit der Schülerliste und korrigiert Fehler."""
    raw_text = " ".join(ocr_results).strip()
    
    if not raw_text:
        return "UNBEKANNT"

    # Suche den ähnlichsten Namen in deiner Datenbank
    # match ist der Name, score ist die Ähnlichkeit (0-100)
    match, score = process.extractOne(raw_text, SCHUELER_DATENBANK)
    
    print(f"  OCR erkannt: '{raw_text}' -> Match: '{match}' (Sicherheit: {score}%)")
    
    # Wenn die Ähnlichkeit über 60% liegt, nehmen wir den Namen aus der Liste
    if score > 60:
        return match.replace(" ", "_")
    
    # Ansonsten nehmen wir das, was die OCR gelesen hat (bereinigt)
    return clean_part(raw_text).replace(" ", "_")

def extract_name(image_path: str, box: tuple) -> list:
    img = Image.open(image_path)
    roi = img.crop(box)
    roi = preprocess_blue_ink(roi)
    roi.save("debug_roi.png")
    
    results = reader.readtext(
        np.array(roi), 
        detail=0, 
        paragraph=True,
        allowlist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß- "
    )
    return results

def process_files():
    supported = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    files = [f for f in os.listdir(INPUT_FOLDER) if os.path.splitext(f)[1].lower() in supported]

    if not files:
        print("Keine Dateien in 'inbox' gefunden.")
        return

    ok, failed = 0, 0

    for file in files:
        path = os.path.join(INPUT_FOLDER, file)
        ext = os.path.splitext(file)[1].lower()
        
        try:
            print(f"\nVerarbeite: {file}...")
            ocr_parts = extract_name(path, NAME_BOX)
            
            # Hier passiert die Magie der Fehlerkorrektur
            final_name = get_best_name_match(ocr_parts)
            
            new_filename = f"{final_name}{ext}"
            new_path = os.path.join(OUTPUT_FOLDER, new_filename)
            
            # Duplikate verhindern (z.B. Test_1.jpg, Test_2.jpg)
            counter = 1
            while os.path.exists(new_path):
                base = os.path.splitext(new_filename)[0]
                new_path = os.path.join(OUTPUT_FOLDER, f"{base}_{counter}{ext}")
                counter += 1
            
            shutil.move(path, new_path)
            print(f"  ✓ Gespeichert als: {os.path.basename(new_path)}")
            ok += 1
        except Exception as e:
            print(f"  ✗ Fehler bei {file}: {e}")
            failed += 1

    print(f"\nFertig! {ok} erfolgreich, {failed} fehlgeschlagen.")

if __name__ == "__main__":
    process_files()