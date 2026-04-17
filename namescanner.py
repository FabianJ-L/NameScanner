import os
import shutil
import easyocr
from PIL import Image, ImageOps
import numpy as np

INPUT_FOLDER = "inbox"
OUTPUT_FOLDER = "sorted"
NAME_BOX = (200, 240, 900, 300)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
reader = easyocr.Reader(["de", "en"], gpu=False)


def preprocess_blue_ink(img: Image.Image) -> Image.Image:
    """Optimiert blaue Tinte auf weißem Hintergrund für OCR."""
    img = img.convert("RGB")
    r, g, b = img.split()
    
    # Blauer Kanal hat bei blauer Tinte WENIGER Signal → invertieren
    # Roter Kanal hat bei blauer Tinte MEHR Kontrast
    # Wir nehmen den roten Kanal allein
    r_arr = np.array(r)
    
    # Invertieren: dunkle Stellen (Tinte) werden hell, helle (Papier) dunkel
    enhanced = 255 - r_arr
    
    result = Image.fromarray(enhanced)
    result = ImageOps.autocontrast(result, cutoff=5)
    
    # 4x Upscale
    w, h = result.size
    result = result.resize((w * 4, h * 4), Image.LANCZOS)
    
    return result


def clean_part(text: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß-")
    return "".join(c for c in text if c in allowed)


def format_filename(parts: list, ext: str) -> str:
    # 1. Alle Strings zu einer Liste von Wörtern flachklopfen
    all_words = []
    for p in parts:
        all_words.extend(p.split())
    
    # 2. Wörter filtern, die offensichtlich Anweisungen sind
    blacklist = {"bitte", "deutlich", "lesbar", "schreiben", "in", "ein"}
    filtered = [w for w in all_words if clean_part(w).lower() not in blacklist and len(clean_part(w)) > 1]
    
    # 3. Nur die ersten beiden sinnvollen Wörter als Namen nehmen (z.B. Nachname_Vorname)
    if not filtered:
        return f"UNBEKANNT{ext}"
    
    # Nimmt maximal die ersten zwei gefundenen "Namensteile"
    name_parts = filtered[:2]
    return f"{'_'.join(name_parts)}{ext}"


def extract_name(image_path: str, box: tuple) -> list:
    img = Image.open(image_path)
    roi = img.crop(box)
    roi = preprocess_blue_ink(roi)
    roi.save("debug_roi.png")  # zum Kontrollieren
    
    tmp_path = "tmp_roi.png"
    roi.save(tmp_path)
    results = reader.readtext(tmp_path, detail=0, paragraph=True)
    os.remove(tmp_path)
    
    print(f"  OCR-Rohtext: {results}")
    return results


def process_files():
    supported = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
    files = [f for f in os.listdir(INPUT_FOLDER)
             if os.path.splitext(f)[1].lower() in supported]

    if not files:
        print("Keine Bilddateien in 'inbox' gefunden.")
        return

    ok, failed = 0, 0

    for file in files:
        path = os.path.join(INPUT_FOLDER, file)
        ext = os.path.splitext(file)[1].lower()

        try:
            parts = extract_name(path, NAME_BOX)
            new_filename = format_filename(parts, ext)

            if "UNBEKANNT" in new_filename:
                failed += 1
            else:
                ok += 1

            new_path = os.path.join(OUTPUT_FOLDER, new_filename)
            counter = 1
            while os.path.exists(new_path):
                base = os.path.splitext(new_filename)[0]
                new_path = os.path.join(OUTPUT_FOLDER, f"{base}_{counter}{ext}")
                counter += 1

            shutil.move(path, new_path)
            print(f"  ✓  {file} → {os.path.basename(new_path)}")

        except Exception as e:
            print(f"  ✗  {file}: {e}")
            failed += 1

    print(f"\n{ok} OK · {failed} fehlgeschlagen")


if __name__ == "__main__":
    process_files()