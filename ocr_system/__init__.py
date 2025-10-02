# __init__.py

# Expose main OCR functions at the package level
from .main import run_ocr_pipeline, get_ocr

# Expose Streamlit CLI (optional, if you want users to access it)
from .cli_streamlit import main as run_streamlit_app

# Optional: define __all__ to control what gets imported with `from ocr_system import *`
__all__ = [
    "run_ocr_pipeline",
    "get_ocr",
    "run_streamlit_app"
]
