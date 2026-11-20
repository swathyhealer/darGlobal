
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv(
    "BASE_URL",
    "https://darglobal.co.uk/"
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3.5-super-vl:free"
)

MAX_PAGES = int(os.getenv("MAX_PAGES", "500"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1"))

ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / "data"
HTML_DIR = DATA_DIR / "html"
EXTRACTED_DIR = DATA_DIR / "extracted"

CSV_FILE = DATA_DIR / "darglobal_data.csv"

for directory in [DATA_DIR, HTML_DIR, EXTRACTED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
