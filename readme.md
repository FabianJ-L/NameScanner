# NameScanner

**NameScanner** is an automated tool designed to process, rename, and sort documents (e.g., test papers) based on handwritten names identified within the document. It utilizes Optical Character Recognition (OCR) and fuzzy matching to ensure high accuracy, even with challenging handwriting.

## How it Works

1. **Input** – The script monitors an `inbox` folder for new image files.
2. **Preprocessing** – It crops the document to a specific area (ROI) and optimizes the image for text recognition, converting blue ink to high-contrast monochrome.
3. **OCR Processing** – The [EasyOCR](https://www.jaided.ai/easyocr/) engine scans the cropped area to extract text.
4. **Intelligent Matching** – Using [TheFuzz](https://github.com/seatgeek/thefuzz), the script compares extracted text against your predefined `REFERENCE_ENTITIES` list to correct common OCR errors (e.g., "FADIAN" → "Fabian").
5. **Sorting** – The file is renamed to `Surname_Firstname.ext` and moved to the `sorted` folder.

## Technologies Used

- **Python 3.11+**
- **[EasyOCR](https://www.jaided.ai/easyocr/)** – Robust text recognition
- **[Pillow (PIL)](https://pillow.readthedocs.io/)** – Image manipulation (cropping, filtering)
- **[NumPy](https://numpy.org/)** – Efficient matrix operations on image data
- **[TheFuzz](https://github.com/seatgeek/thefuzz)** – Fuzzy string matching and error correction

## Installation

1. **Install Python** – Ensure Python 3.11 or later is installed on your system.
2. **Install Dependencies** – Open your terminal or command prompt in the project folder and run:
   ```bash
   pip install easyocr pillow numpy thefuzz python-Levenshtein
   ```

## Usage

### 1. Configure the Reference List

Open `namescanner.py` and update the `REFERENCE_ENTITIES` list with your class names:

```python
REFERENCE_ENTITIES = [
    "Janisch-Lang Fabian",
    "Häusler Valentin",
    # Add your students here
]
```

### 2. Adjust Coordinates

If the name field's position changes, update the `TARGET_AREA_COORDS` variable (left, top, right, bottom). Always verify the generated `debug_roi.png` to ensure the name area is captured correctly.

### 3. Run the Scanner

Place your images into the `inbox` folder and execute the script:

```bash
python namescanner.py
```

## Project Structure

- **inbox/** – Place your raw scans here
- **sorted/** – Your processed, renamed files will appear here
- **namescanner.py** – Main application script
- **debug_roi.png** – Visual check file to verify your coordinate settings