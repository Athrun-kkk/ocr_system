import os
import json
from paddleocr import PaddleOCR
from ocr_system.helpers import (
    create_project,
    register_image,
    save_ocr_texts,
    save_ocr_outputs,
    update_image_status,
    generate_ocr_overlay,
)
from ocr_system.orm_models import Session, init_db

# ------------------------
# Global OCR instance (lazy init)
# ------------------------
_OCR_INSTANCE = None

def get_model_path(subdir):
    # Priority: env var, else fallback to ./models
    base = os.environ.get("OCR_SYSTEM_MODELS", os.path.join(os.getcwd(), "models"))
    return os.path.join(base, subdir)

def get_ocr():
    """Initialize PaddleOCR once and reuse it."""
    global _OCR_INSTANCE
    if _OCR_INSTANCE is None:
        _OCR_INSTANCE = PaddleOCR(
            lang="en",
            text_detection_model_dir=get_model_path("PP-OCRv5_server_det"),
            text_recognition_model_dir=get_model_path("PP-OCRv5_server_rec"),
            doc_unwarping_model_dir=get_model_path("UVDoc"),
            textline_orientation_model_dir=get_model_path("PP-LCNet_x1_0_textline_ori"),
            doc_orientation_classify_model_dir=get_model_path("PP-LCNet_x1_0_doc_ori"),
        )
    return _OCR_INSTANCE

def run_ocr_pipeline(input_root, output_root, project_name, pdf_only=True, use_streamlit=False, st=None):
    """
    Run OCR pipeline for a given project.

    Args:
        input_root (str): Root folder for input images.
        output_root (str): Root folder for OCR outputs.
        project_name (str): Project name (also subfolder name under input/output).
        pdf_only (bool): Whether to save only PDF outputs.
        use_streamlit (bool): If True, display progress in Streamlit.
        st (module): Streamlit module (required if use_streamlit=True).
    """
    os.makedirs(output_root, exist_ok=True)

    # Initialize DB
    init_db()
    session = Session()

    # Get shared OCR instance
    ocr = get_ocr()

    # Explicit Project
    project = create_project(session, project_name, base_path=os.path.join(input_root, project_name))

    project_input_dir = os.path.join(input_root, project_name)
    if not os.path.exists(project_input_dir):
        msg = f"Input folder not found: {project_input_dir}"
        if use_streamlit:
            st.error(msg)
        else:
            print(msg)
        return

    image_files = [
        f for f in os.listdir(project_input_dir)
        if os.path.isfile(os.path.join(project_input_dir, f))
        and f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff"))
    ]

    progress = None
    if use_streamlit:
        progress = st.progress(0)

    total = len(image_files)
    for idx, fname in enumerate(image_files, 1):
        fpath = os.path.join(project_input_dir, fname)
        log_msg = f"Processing {fname} ..."
        if use_streamlit:
            st.write(f"Processing **{fname}** ...")
        else:
            print(log_msg)

        # Register image in DB
        image = register_image(
            session,
            project.id,
            filename=fname,
            output_dir=os.path.join(output_root, project_name),
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
                        "rec_boxes": [line["box"] for line in ocr_results],
                    }, f, ensure_ascii=False, indent=2)

            # Save output files info to DB
            save_ocr_outputs(session, image, output_paths, pdf_only=pdf_only)

            # Update status
            update_image_status(session, image, "processed")

            if use_streamlit:
                st.success(f"Done: {fname}")
            else:
                print(f"Done: {fname}, OCR results saved.\n")

        except Exception as e:
            err_msg = f"Error processing {fname}: {e}"
            if use_streamlit:
                st.error(err_msg)
            else:
                print(err_msg)
            update_image_status(session, image, "failed")

        if use_streamlit and progress:
            progress.progress(idx / total)

    if use_streamlit:
        st.success("OCR processing finished!")
    else:
        print("OCR processing finished!")


# CLI entrypoint (optional)
def cli():
    import argparse

    parser = argparse.ArgumentParser(description="Run OCR pipeline")
    parser.add_argument("--input", required=True, help="Input root folder")
    parser.add_argument("--output", required=True, help="Output root folder")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--pdf-only", action="store_true", help="Save only PDF")
    args = parser.parse_args()

    run_ocr_pipeline(
        input_root=args.input,
        output_root=args.output,
        project_name=args.project,
        pdf_only=args.pdf_only,
    )


if __name__ == "__main__":
    cli()
