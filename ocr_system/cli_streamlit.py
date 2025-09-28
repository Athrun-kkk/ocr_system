import subprocess
import os
import sys

def main():
    """Launch the Streamlit OCR app."""
    app_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    subprocess.run(cmd)
