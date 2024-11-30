from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pdfplumber
import hashlib
from src.ai_handler import ChatGPTHandler
from src.pdf_parser import find_toc_pages, parse_table_of_contents, find_page_offset, extract_chapter_sections
import os

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_handler = ChatGPTHandler()

class ChapterRequest(BaseModel):
    pdf_hash: str
    chapter: int

def compute_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()

@app.post("/process_pdf")
async def process_pdf(file: UploadFile = File(...)):
    """Process PDF and return structured data without storing"""
    contents = await file.read()
    pdf_hash = compute_hash(contents)
    
    # Store temporarily for processing
    temp_path = f"temp/{pdf_hash}_{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        with pdfplumber.open(temp_path) as pdf:
            # Process TOC
            toc_pages = find_toc_pages(pdf)
            last_toc_page = max(toc_pages) if toc_pages else 0
            toc_content = parse_table_of_contents(pdf)
            structured_toc = ai_handler.process_toc(toc_content)
            page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)
            
            return {
                "status": "success",
                "pdf_hash": pdf_hash,
                "filename": file.filename,
                "toc": structured_toc.model_dump(),
                "page_offset": page_offset
            }
    
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/generate_chapter_questions")
async def generate_chapter_questions(file: UploadFile = File(...), chapter: int = 1):
    """Generate questions for a specific chapter"""
    contents = await file.read()
    pdf_hash = compute_hash(contents)
    
    temp_path = f"temp/{pdf_hash}_{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as f:
            f.write(contents)
            
        with pdfplumber.open(temp_path) as pdf:
            # Process TOC first
            toc_content = parse_table_of_contents(pdf)
            structured_toc = ai_handler.process_toc(toc_content)
            toc_pages = find_toc_pages(pdf)
            last_toc_page = max(toc_pages) if toc_pages else 0
            page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)
            
            # Generate questions for the specified chapter
            sections = extract_chapter_sections(pdf, structured_toc.model_dump(), page_offset, chapter)
            
            all_questions = []
            for section_number, content in sections.items():
                questions = ai_handler.generate_questions(content)
                all_questions.extend(questions.questions)
            
            return {
                "pdf_hash": pdf_hash,
                "chapter": chapter,
                "questions": all_questions
            }
    
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
