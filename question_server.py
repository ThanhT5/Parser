from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pdfplumber
import os
import hashlib
import json
from pathlib import Path
from src.ai_handler import ChatGPTHandler
from src.pdf.parser import (
    parse_table_of_contents,
    extract_chapter_sections,
)
from src.pdf.toc_detector import find_toc_pages
from src.pdf.page_analyzer import find_page_offset
from src.exceptions.pdf_exceptions import PDFExtractionError, TOCNotFoundError
import uuid


app = FastAPI()


# Define storage directory and file
STORAGE_DIR = Path("data")
STORAGE_FILE = STORAGE_DIR / "pdf_metadata.json"


# Create storage directory if it doesn't exist
STORAGE_DIR.mkdir(exist_ok=True)


# Initialize or load PDF data from storage
def load_pdf_data():
    if STORAGE_FILE.exists():
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_pdf_data(data):
    with open(STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=4)


# Load existing data on startup
pdf_data = load_pdf_data()


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


ai_handler = ChatGPTHandler()


def get_pdf_hash(contents: bytes) -> str:
    """Generate a hash for PDF contents to use as identifier"""
    return hashlib.sha256(contents).hexdigest()


@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Parser API!"}


@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Process PDF and store structured TOC data"""
    contents = await file.read()
    pdf_hash = get_pdf_hash(contents)
   
    # Check if we already have the data
    if pdf_hash in pdf_data:
        return {
            "status": "success",
            "message": "PDF already processed",
            "toc": pdf_data[pdf_hash]["toc"],
            "page_offset": pdf_data[pdf_hash]["page_offset"]
        }
   
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
   
    try:
        # Save temporarily for processing
        with open(temp_path, "wb") as f:
            f.write(contents)
       
        with pdfplumber.open(temp_path) as pdf:
            try:
                # Process TOC
                toc_pages = find_toc_pages(pdf)
                if not toc_pages:
                    raise TOCNotFoundError("No table of contents found in the document")
                   
                last_toc_page = max(toc_pages)
                toc_content = parse_table_of_contents(pdf, toc_pages)
                structured_toc = ai_handler.process_toc(toc_content)
                page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)
               
                # Store the data
                pdf_data[pdf_hash] = {
                    "toc": structured_toc.model_dump(),
                    "page_offset": page_offset,
                    "filename": file.filename  # Store filename for reference
                }
                # Persist to file
                save_pdf_data(pdf_data)
               
                return {
                    "status": "success",
                    "toc": structured_toc.model_dump(),
                    "page_offset": page_offset
                }
            except (PDFExtractionError, TOCNotFoundError) as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
   
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/list_processed_pdfs")
async def list_processed_pdfs():
    """List all processed PDFs and their metadata"""
    return {
        "status": "success",
        "pdfs": [
            {
                "hash": pdf_hash,
                "filename": data.get("filename", "Unknown"),
                "has_toc": bool(data.get("toc")),
                "page_offset": data.get("page_offset")
            }
            for pdf_hash, data in pdf_data.items()
        ]
    }


@app.post("/generate_questions")
async def generate_questions(
    file: UploadFile = File(...),
    chapter: int = 1,
    total_questions: int = 30
):
    """
    Generate questions for a specific chapter using stored TOC data.
   
    Args:
        file: PDF file upload
        chapter: Chapter number to generate questions for
        total_questions: Total number of questions to generate for the chapter
   
    Returns:
        JSON response containing generated questions or error message
    """
    contents = await file.read()
    pdf_hash = get_pdf_hash(contents)
   
    if pdf_hash not in pdf_data:
        return {
            "status": "error",
            "message": "PDF not processed. Please upload the PDF with /upload_pdf first."
        }
   
    stored_data = pdf_data[pdf_hash]
    temp_path = f"temp_{uuid.uuid4()}_{file.filename}"
   
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
           
        with pdfplumber.open(temp_path) as pdf:
            try:
                # Extract sections and get question distribution
                print(chapter)
                sections, question_distribution = extract_chapter_sections(
                    pdf,
                    stored_data["toc"],
                    stored_data["page_offset"],
                    chapter,
                    total_questions=total_questions
                )
               
                # Generate questions for each section based on distribution
                all_questions = []
                for section_number, content in sections.items():
                    num_questions = question_distribution[section_number]
                    section_questions = ai_handler.generate_questions(content, num_questions)
                   
                    # Add section information to each question
                    for question in section_questions.questions:
                        question_with_section = question.dict()
                        question_with_section["section"] = section_number
                        all_questions.append(question_with_section)
               
                return {
                    "status": "success",
                    "chapter": chapter,
                    "questions": all_questions,
                    "distribution": question_distribution
                }
            except PDFExtractionError as e:
                return {
                    "status": "error",
                    "message": str(e)
                }
   
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



