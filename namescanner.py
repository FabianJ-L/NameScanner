import os
import shutil
import easyocr
from PIL import Image

INPUT_FOLDER = "inbox"
OUTPUT_FOLDER = "sorted"
NAME_BOX = (239, 243, 840, 291)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Einmalig laden (dauert beim ersten Mal ~30 Sekunden)
reader = easyocr.Reader(["de", "en"], gpu=False)


def clean_part(text: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜäöüß-")
    return "".join(c for c in text if c in allowed)


def format_filename(parts: list[str], ext: str) -> str:
    parts = [clean_part(p) for p in parts if clean_part(p)]

    if len(parts) == 0:
        return f"UNBEKANNT{ext}"
    elif len(parts) == 1:
        return f"{parts[0]}{ext}"
    elif len(parts) == 2:
        vorname, nachname = parts[0], parts[1]
        if "-" in vorname and "-" not in nachname:
            vorname, nachname = nachname, vorname
        return f"{nachname}_{vorname}{ext}"
    else:
        nachname = parts[-1]
        vorname = "_".join(parts[:-1])
        return f"{nachname}_{vorname}{ext}"


def extract_name(image_path: str, box: tuple) -> list[str]:
    img = Image.open(image_path)
    roi = img.crop(box)

    # Upscale für bessere Erkennung
    w, h = roi.size
    roi = roi.resize((w * 4, h * 4), Image.LANCZOS)

    # Temporär speichern für EasyOCR
    tmp_path = "tmp_roi.png"
    roi.save(tmp_path)

    results = reader.readtext(tmp_path, detail=0, paragraph=False)
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