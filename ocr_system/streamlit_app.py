import streamlit as st
from main import run_ocr_pipeline, get_ocr

def main():
    st.title("OCR Processing App (PaddleOCR)")

    input_root = st.text_input("Input root folder", "./demo_photos")
    output_root = st.text_input("Output root folder", "./output_OCRv5")
    pdf_only = st.checkbox("Save only PDF", value=True)
    project_name = st.text_input("Project name", "project_1")

    if st.button("Run OCR"):
        # Ensure OCR is initialized once
        get_ocr()
        run_ocr_pipeline(
            input_root=input_root,
            output_root=output_root,
            project_name=project_name,
            pdf_only=pdf_only,
            use_streamlit=True,
            st=st,
        )

if __name__ == "__main__":
    main()
