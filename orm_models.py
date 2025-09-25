from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# ------------------------
# Project Table
# ------------------------
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    base_path = Column(String)  # optional: maps to input folder
    created_at = Column(DateTime, default=datetime.utcnow)

    images = relationship("Image", back_populates="project")


# ------------------------
# Image Table
# ------------------------
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    filename = Column(String)
    relative_path = Column(String)   # path relative to project
    output_dir = Column(String)      # where OCR outputs are stored
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    ocr_finished_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="images")


# ------------------------
# OCRText Table
# ------------------------
class OCRText(Base):
    __tablename__ = "ocr_texts"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    text = Column(String)
    confidence = Column(String)
    x1 = Column(Integer)
    y1 = Column(Integer)
    x2 = Column(Integer)
    y2 = Column(Integer)


# ------------------------
# OCROutput Table
# ------------------------
class OCROutput(Base):
    __tablename__ = "ocr_outputs"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"))
    file_type = Column(String)  # json/pdf/jpg
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ------------------------
# Database Setup
# ------------------------
DATABASE_URL = "sqlite:///./ocr_demo.db"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
