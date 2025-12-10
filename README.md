# OCR Processing Toolkit (PaddleOCR PP-OCRv5)

This toolkit provides a full OCR pipeline using PaddleOCR PP-OCRv5. It supports batch image OCR, searchable PDF generation, overlay visualization, JSON output, and process logging into an SQLite database. Both a CLI and Streamlit frontend are included.

---

## Features

- Batch OCR for entire project folders.
- Extracts text, confidence scores, and bounding box coordinates.
- Output options:
  - Searchable PDF (if `pdf_only=True`)
  - OCR overlay images with text detection boxes
  - JSON output for recognized text data (if `pdf_only=False`)
- SQLite database for:
  - image-level records
  - OCR text lines
  - status tracking
  - generated file paths
- PaddleOCR initialized once and reused for efficiency.
- Local model usage supported for offline deployment.
- CLI and Streamlit UI both available.

---
