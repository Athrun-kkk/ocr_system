import os
import json
import streamlit as st
from paddleocr import PaddleOCR
from helpers import (
    create_project,
    register_image,
    save_ocr_texts,
    save_ocr_outputs,
    update_image_status,
    generate_ocr_overlay
)
from orm_models import Session, init_db

# ------------------------
# Streamlit UI
# ------------------------
st.title("OCR Processing App (PaddleOCR)")

input_root = st.text_input("Input root folder", "./demo_photos")
output_root = st.text_input("Output root folder", "./output_OCRv5")
pdf_only = st.checkbox("Save only PDF", value=True)

project_name = st.text_input("Project name", "project_1")

run_btn = st.button("Run OCR")

if run_btn:
    os.makedirs(output_root, exist_ok=True)

    # Initialize DB
    init_db()
    session = Session()

    # Initialize OCR
    ocr = PaddleOCR(
        lang="en",
        text_detection_model_name="PP-OCRv5_server_det",
        text_recognition_model_name="PP-OCRv5_server_rec",
        use_doc_orientation_classify=False,
        use_doc_unwarping=True,
        use_textline_orientation=True
    )

    st.write(f"### Running OCR for project: {project_name}")

    # Explicit Project (user-defined)
    project = create_project(session, project_name, base_path=os.path.join(input_root, project_name))

    project_input_dir = os.path.join(input_root, project_name)
    if not os.path.exists(project_input_dir):
        st.error(f"Input folder not found: {project_input_dir}")
    else:
        image_files = [f for f in os.listdir(project_input_dir)
                       if os.path.isfile(os.path.join(project_input_dir, f))
                       and f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff"))]

        progress = st.progress(0)
        total = len(image_files)

        for idx, fname in enumerate(image_files, 1):
            fpath = os.path.join(project_input_dir, fname)
            st.write(f"Processing **{fname}** ...")

            # Register image in DB
            image = register_image(
                session,
                project.id,
                filename=fname,
                output_dir=os.path.join(output_root, project_name)
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

                # Save overlay and outputs
                output_paths = generate_ocr_overlay(
                    fpath, ocr_results, output_root, project_name, pdf_only=pdf_only
                )

                # Save JSON if not pdf_only
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
                st.success(f"Done: {fname}")

            except Exception as e:
                st.error(f"Error processing {fname}: {e}")
                update_image_status(session, image, "failed")

            progress.progress(idx / total)

        st.success("OCR processing finished!")
