import os
import json
from paddleocr import PaddleOCR
from helpers import (
    create_project,
    register_image,
    save_ocr_texts,
    save_ocr_outputs,
    update_image_status,
    generate_ocr_overlay
)
from orm_models import Session, init_db, Image

# ------------------------
# Settings
# ------------------------
input_root = "./demo_photos"
output_root = "./output_OCRv5"
os.makedirs(output_root, exist_ok=True)

# Toggle: save only PDF (True) or full outputs (False)
pdf_only = True 

# ------------------------
# Initialize DB
# ------------------------
init_db()
session = Session()

# ------------------------
# Initialize OCR
# ------------------------
ocr = PaddleOCR(
    lang="en",
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=True,
    use_textline_orientation=True
)

# ------------------------
# Explicit Project (user-defined)
# ------------------------
project_name = "project_1"
project = create_project(session, project_name, base_path=os.path.join(input_root, project_name))

project_input_dir = os.path.join(input_root, project_name)
for fname in os.listdir(project_input_dir):
    fpath = os.path.join(project_input_dir, fname)
    if not os.path.isfile(fpath):
        continue
    if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
        continue

    print(f"Processing {fname} ...")

    # Register image in DB
    image = register_image(
        session,
        project.id,
        filename=fname,
        output_dir=os.path.join(output_root, project_name)  # no per-image folder
    )

    try:
        # Run OCR
        result = ocr.predict(fpath)

        # Extract results
        ocr_results = []
        for res in result:
            rec_texts = res.get("rec_texts", [])
            rec_scores = res.get("rec_scores", [])
            rec_boxes = res.get("rec_boxes", [])
            for text, score, box in zip(rec_texts, rec_scores, rec_boxes):
                ocr_results.append({
                    "text": text,
                    "confidence": score,
                    "box": box.tolist() if hasattr(box, "tolist") else box
                })

        # Save OCR texts to DB
        save_ocr_texts(session, image, ocr_results)

        # Save overlay and outputs (pdf_only controls file creation)
        output_paths = generate_ocr_overlay(
            fpath, ocr_results, output_root, project_name, pdf_only=pdf_only
        )

        # Save JSON result file if not pdf_only
        if not pdf_only and "json" in output_paths:
            with open(output_paths["json"], "w", encoding="utf-8") as f:
                json.dump({
                    "rec_texts": [line["text"] for line in ocr_results],
                    "rec_scores": [line["confidence"] for line in ocr_results],
                    "rec_boxes": [line["box"] for line in ocr_results]
                }, f, ensure_ascii=False, indent=2)

        # Save output files info to DB
        save_ocr_outputs(session, image, output_paths, pdf_only=pdf_only)

        # Update status
        update_image_status(session, image, "processed")
        print(f"Done: {fname}, OCR results saved.\n")

    except Exception as e:
        print(f"Error processing {fname}: {e}")
        update_image_status(session, image, "failed")
