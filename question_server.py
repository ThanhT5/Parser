# Import necessary libraries and modules
from fastapi import FastAPI, File, UploadFile, HTTPException  # FastAPI for building APIs
from pydantic import BaseModel  # Pydantic for data validation
from typing import List  # For type hinting lists
import uvicorn  # ASGI server for running the app
import sqlite3  # SQLite for database operations
import pdfplumber  # Library for PDF processing
from src.ai_handler import ChatGPTHandler, TOCStructure, Questions  # Custom AI handler for processing
from src.pdf_parser import find_toc_pages, parse_table_of_contents, find_page_offset, extract_chapter_sections  # PDF parsing functions
import io  # For handling byte streams

# Initialize FastAPI application
app = FastAPI()
# Create an instance of the ChatGPTHandler to interact with the AI
ai_handler = ChatGPTHandler()

# Define request model for chapter requests
class ChapterRequest(BaseModel):
    pdf_id: str  # ID of the PDF document
    chapter: int  # Chapter number


# SQLite database setup
DATABASE_NAME = "textbook_questions.db"  # Name of the SQLite database

# Function to initialize the database and create necessary tables
def init_db():
    conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
    cursor = conn.cursor()  # Create a cursor object to execute SQL commands
    # Create table for storing PDF information
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pdf_info
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     filename TEXT,
     toc TEXT,
     page_offset INTEGER)
    ''')
    # Create table for storing questions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
     pdf_id INTEGER,
     chapter INTEGER,
     question TEXT,
     answer TEXT,
     FOREIGN KEY (pdf_id) REFERENCES pdf_info(id))
    ''')
    conn.commit()  # Commit the changes
    conn.close()  # Close the database connection

# Initialize the database
init_db()

# Endpoint to upload a PDF file
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()  # Read the contents of the uploaded file
    pdf_stream = io.BytesIO(contents)  # Create a byte stream from the contents
    
    # Open the PDF file using pdfplumber
    with pdfplumber.open(pdf_stream) as pdf:
        # Find TOC pages and parse TOC content
        toc_pages = find_toc_pages(pdf)  # Get the pages that contain the TOC
        last_toc_page = max(toc_pages) if toc_pages else 0  # Get the last TOC page
        toc_content = parse_table_of_contents(pdf)  # Parse the TOC content

        # Process TOC with ChatGPT to structure it
        structured_toc = ai_handler.process_toc(toc_content)

        # Find page offset for the TOC
        page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)

    # Store the PDF information in SQLite
    pdf_id = store_pdf_info(file.filename, structured_toc.model_dump(), page_offset)
    
    # Return the PDF ID, structured TOC, and page offset
    return {"pdf_id": pdf_id, "toc": structured_toc, "page_offset": page_offset}

# Endpoint to generate questions based on a chapter
@app.post("/generate_questions")
async def generate_questions(request: ChapterRequest):
    # Retrieve PDF info from SQLite using the provided PDF ID
    pdf_info = get_pdf_info(request.pdf_id)
    if not pdf_info:
        raise HTTPException(status_code=404, detail="PDF not found")  # Raise error if PDF not found
    
    filename, toc_str, page_offset = pdf_info  # Unpack PDF info
    toc = TOCStructure.model_validate_json(toc_str)  # Validate and parse TOC structure

    # Check if questions already exist for the chapter
    existing_questions = get_questions(request.pdf_id, request.chapter)
    if existing_questions:
        return {"questions": existing_questions}  # Return existing questions if found

    # If questions don't exist, generate them
    with pdfplumber.open(filename) as pdf:
        sections = extract_chapter_sections(pdf, toc.model_dump(), page_offset, request.chapter)  # Extract sections for the chapter
        
        all_questions = []  # List to hold all generated questions
        for section_number, content in sections.items():
            questions = ai_handler.generate_questions(content)  # Generate questions for each section
            all_questions.extend(questions.questions)  # Add generated questions to the list

    # Store the generated questions in SQLite
    store_questions(request.pdf_id, request.chapter, all_questions)
    
    return {"questions": all_questions}  # Return the generated questions

# SQLite helper functions

# Function to store PDF information in the database
def store_pdf_info(filename, toc, page_offset):
    conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
    cursor = conn.cursor()  # Create a cursor object
    # Insert PDF information into the database
    cursor.execute("INSERT INTO pdf_info (filename, toc, page_offset) VALUES (?, ?, ?)",
                   (filename, TOCStructure(entries=toc['entries']).model_dump_json(), page_offset))
    pdf_id = cursor.lastrowid  # Get the ID of the last inserted row
    conn.commit()  # Commit the changes
    conn.close()  # Close the database connection
    return pdf_id  # Return the PDF ID

# Function to retrieve PDF information from the database
def get_pdf_info(pdf_id):
    conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
    cursor = conn.cursor()  # Create a cursor object
    # Query to get PDF information by ID
    cursor.execute("SELECT filename, toc, page_offset FROM pdf_info WHERE id = ?", (pdf_id,))
    result = cursor.fetchone()  # Fetch the result
    conn.close()  # Close the database connection
    return result if result else None  # Return the result or None if not found

# Function to store generated questions in the database
def store_questions(pdf_id, chapter, questions):
    conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
    cursor = conn.cursor()  # Create a cursor object
    # Insert each question into the database
    for question in questions:
        cursor.execute("INSERT INTO questions (pdf_id, chapter, question, answer) VALUES (?, ?, ?, ?)",
                       (pdf_id, chapter, question.question, question.answer))
    conn.commit()  # Commit the changes
    conn.close()  # Close the database connection

# Function to retrieve questions from the database
def get_questions(pdf_id, chapter):
    conn = sqlite3.connect(DATABASE_NAME)  # Connect to the database
    cursor = conn.cursor()  # Create a cursor object
    # Query to get questions by PDF ID and chapter
    cursor.execute("SELECT question, answer FROM questions WHERE pdf_id = ? AND chapter = ?", (pdf_id, chapter))
    results = cursor.fetchall()  # Fetch all results
    conn.close()  # Close the database connection
    return [{"question": q, "answer": a} for q, a in results]  # Return the results as a list of dictionaries

# Entry point for running the application
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Run the FastAPI application
