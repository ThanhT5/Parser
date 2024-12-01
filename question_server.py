from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pdfplumber
import os
from src.ai_handler import ChatGPTHandler
from src.pdf_parser import find_toc_pages, parse_table_of_contents, find_page_offset, extract_chapter_sections


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

@app.get("/")
async def root():
    return {"message": "Welcome to the PDF Processing API"}

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Process PDF and return structured TOC data"""
    contents = await file.read()
    temp_path = f"temp_{file.filename}"
   
    try:
        # Save temporarily for processing
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
                "toc": structured_toc.model_dump(),
                "page_offset": page_offset
            }
   
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/generate_questions")
async def generate_questions(file: UploadFile = File(...), chapter: int = 1):
    """Generate questions for a specific chapter"""
    contents = await file.read()
    temp_path = f"temp_{file.filename}"
   
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
           
            questions = []
            for section_number, content in sections.items():
                section_questions = ai_handler.generate_questions(content)
                questions.extend(section_questions.questions)
           
            return {
                "status": "success",
                "chapter": chapter,
                "questions": questions
            }
   
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)



