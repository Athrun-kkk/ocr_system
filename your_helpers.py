import os
import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as patches
from datetime import datetime
from sqlalchemy.orm import Session
from your_orm_models import Project, Image, OCRText, OCROutput

from matplotlib import rcParams
rcParams['font.family'] = 'Microsoft YaHei'

# ------------------------
# Project Management
# ------------------------
def create_project(session, name, base_path=None):
    project = session.query(Project).filter_by(name=name).first()
    if project:
        return project  # reuse existing instead of creating a new one
    
    project = Project(name=name, base_path=base_path)
    session.add(project)
    session.commit()
    return project



# ------------------------
# Image Registration
# ------------------------
def register_image(session: Session, project_id: int, filename: str, output_dir: str):
    project = session.query(Project).filter_by(id=project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} does not exist!")

    image = Image(
        project_id=project.id,
        filename=filename,
        relative_path=filename,
        output_dir=output_dir,
        status="pending"
    )
    session.add(image)
    session.commit()
    return image


# ------------------------
# Save OCR Texts
# ------------------------
def save_ocr_texts(session: Session, image: Image, ocr_results: list):
    session.query(OCRText).filter(OCRText.image_id == image.id).delete()
    for line in ocr_results:
        text_obj = OCRText(
            image_id=image.id,
            text=line["text"],
            confidence=str(line.get("confidence", "")),
            x1=line["box"][0],
            y1=line["box"][1],
            x2=line["box"][2],
            y2=line["box"][3]
        )
        session.add(text_obj)
    session.commit()


# ------------------------
# Save OCR Outputs
# ------------------------
def save_ocr_outputs(session: Session, image: Image, outputs: dict, pdf_only: bool = False):
    """
    Save OCR outputs info into DB.
    If pdf_only=True, only the PDF entry is saved.
    """
    session.query(OCROutput).filter(OCROutput.image_id == image.id).delete()

    # Always save PDF
    if "pdf" in outputs:
        session.add(OCROutput(
            image_id=image.id,
            file_type="pdf",
            file_path=os.path.abspath(outputs["pdf"]),
            created_at=datetime.utcnow()
        ))

    if not pdf_only:
        if "img" in outputs:
            session.add(OCROutput(
                image_id=image.id,
                file_type="img",
                file_path=os.path.abspath(outputs["img"]),
                created_at=datetime.utcnow()
            ))
        if "json" in outputs:
            session.add(OCROutput(
                image_id=image.id,
                file_type="json",
                file_path=os.path.abspath(outputs["json"]),
                created_at=datetime.utcnow()
            ))

    session.commit()


# ------------------------
# Update Status
# ------------------------
def update_image_status(session: Session, image: Image, status: str, finished_at: datetime = None):
    image.status = status
    image.ocr_finished_at = finished_at or datetime.utcnow()
    session.commit()


# ------------------------
# Generate OCR Overlay
# ------------------------
def generate_ocr_overlay(img_path, ocr_results, output_root, project_name, pdf_only=False):
    """
    Save OCR overlay under project folder:
      output_root/project_name/{image_ocr.pdf, image_ocr.jpg, image_ocr.json}
    If pdf_only=True, only the PDF file is saved.
    """
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    project_folder = os.path.join(output_root, project_name)
    os.makedirs(project_folder, exist_ok=True)

    pdf_path = os.path.join(project_folder, f"{base_name}_ocr.pdf")
    img_path_out = os.path.join(project_folder, f"{base_name}_ocr.jpg")
    json_path_out = os.path.join(project_folder, f"{base_name}_ocr.json")

    # Load original image
    img = mpimg.imread(img_path)
    img_height, img_width = img.shape[0], img.shape[1]

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Original
    ax1.imshow(img)
    ax1.set_title("Original Image")
    ax1.axis("off")

    # Right: OCR Overlay
    ax2.set_xlim(0, img_width)
    ax2.set_ylim(img_height, 0)
    ax2.set_title("OCR Overlay")
    ax2.axis("off")

    for line in ocr_results:
        text = line["text"]
        x1, y1, x2, y2 = line["box"]
        rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1,
                                 linewidth=1, edgecolor='r', facecolor='none')
        ax2.add_patch(rect)
        ax2.text(x1, y1, text, fontsize=12, va="top", ha="left",
                 bbox=dict(facecolor="white", alpha=0.5, edgecolor="none"))

    plt.tight_layout()
    fig.savefig(pdf_path, dpi=150)
    if not pdf_only:
        fig.savefig(img_path_out, dpi=150)
    plt.close(fig)

    outputs = {"pdf": pdf_path}
    if not pdf_only:
        outputs.update({"img": img_path_out, "json": json_path_out})

    return outputs
