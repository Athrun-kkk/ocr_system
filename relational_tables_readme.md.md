# Project-First OCR System

This repository contains a prototype OCR system built with **PaddleOCR**, **SQLAlchemy**, and **Matplotlib**, designed to process images in a project-first folder structure. The system stores OCR results in a database and generates multiple outputs per image (JSON, PDF, annotated image).

---

## Table of Contents

1. [System Overview](#system-overview)  
2. [Directory Structure](#directory-structure)  
3. [Database Schema](#database-schema)  
4. [Input / Output Formats](#input--output-formats)  
5. [Setup and Usage](#setup-and-usage)  
6. [Future Enhancements](#future-enhancements)  

---

## System Overview

- **Project-First Design**: Users define a project (top-level folder) containing images.  
- **OCR Pipeline**: For each image, the system:
  1. Adds image record to the database
  2. Runs OCR with PaddleOCR
  3. Saves OCR texts in the database
  4. Generates overlay images (original + OCR annotations)
  5. Saves outputs (JSON, PDF, annotated image) in a structured folder
  6. Updates image processing status

- **Helper functions**: `add_image`, `save_ocr_texts`, `save_ocr_outputs`, `update_image_status`, `generate_ocr_overlay`

---

## Directory Structure
```
project-root/
├─ demo_photos/ # Input root
│ ├─ project_1/ # Project folder (user-defined)
│ │ ├─ img1.jpg
│ │ ├─ img2.png
│ │ └─ img3.jpg
│ └─ project_2/
│ └─ ...
├─ output_OCRv5/ # Output root
│ ├─ project_1/
│ │ ├─ img1/
│ │ │ ├─ img1_ocr.json
│ │ │ ├─ img1_ocr.pdf
│ │ │ └─ img1_ocr.jpg
│ │ ├─ img2/
│ │ │ └─ ...
│ │ └─ img3/
│ │ └─ ...
│ └─ project_2/
│ └─ ...
├─ app.py
├─ your_helpers.py
├─ your_orm_models.py
└─ requirements.txt
```
---

## Database Schema

### Tables and Relationships

1. **Project**
   - `id` (PK), `name`, `path`, `created_at`
   - **1-to-many → Images**

2. **Image**
   - `id` (PK), `project_id` (FK), `file_name`, `file_path`, `status`, `ocr_model`, `ocr_parameters`, `ocr_finished_at`
   - **1-to-many → OCRText**
   - **1-to-many → OCROutput**

3. **OCRText**
   - `id` (PK), `image_id` (FK), `text`, `confidence`, `x1`, `y1`, `x2`, `y2`

4. **OCROutput**
   - `id` (PK), `image_id` (FK), `file_type` (`json`, `pdf`, `annotated_img`), `file_path`, `created_at`

**Relationships:**
```
Project
│
├── Images
│
├── OCRText
│
└── OCROutput
```
---

## Input / Output Formats

- **Input**: Images in formats `jpg`, `jpeg`, `png`, `bmp`, `tiff` under a project folder.  
- **Output**: For each image:
  - `*_ocr.json` → OCR extracted texts, confidence, bounding boxes  
  - `*_ocr.pdf` → Overlay figure showing original image + OCR annotations  
  - `*_ocr.jpg` → Annotated image  

- **Output folder hierarchy** mirrors the input project folder structure.

---