from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = STATIC_DIR / "templates"
TEMP_DIR = STATIC_DIR / "temp"
OUTPUT_DIR = STATIC_DIR / "output"
FONTS_DIR = STATIC_DIR / "fonts"

# default filenames
TEMPLATE_FILENAME = "template.png"
EXCEL_FILENAME = "data.xlsx"
