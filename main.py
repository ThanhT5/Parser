import os
import json
from src.pdf_parser import find_page_offset, find_toc_pages, INPUT_DIR, OUTPUT_DIR, extract_chapter_sections
from src.ai_handler import ChatGPTHandler
import pdfplumber

def load_structured_toc(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # List of books to process
    books = ["Book1"]#, "Book2", "Book4"]
    
    for book in books:
        pdf_path = os.path.join(INPUT_DIR, f"{book}.pdf")
        toc_json_path = os.path.join(OUTPUT_DIR, f"structured_toc_{book}.json")
        
        print(f"Processing {book}")
        
        if not os.path.exists(pdf_path):
            print(f"Error: The file {pdf_path} does not exist.")
            continue
        
        if not os.path.exists(toc_json_path):
            print(f"Error: The structured TOC file {toc_json_path} does not exist.")
            continue
        
        try:
            # Load the structured TOC
            structured_toc = load_structured_toc(toc_json_path)
            
            # Find the page offset
            with pdfplumber.open(pdf_path) as pdf:
                toc_pages = find_toc_pages(pdf)
                print(f"TOC pages: {toc_pages}")
                last_toc_page = max(toc_pages) if toc_pages else 0
                page_offset = find_page_offset(pdf, structured_toc, last_toc_page)
            
            print(f"Page offset for {book}: {page_offset}")

            # Get the chapter number from user input
            chapter = int(input("Enter the chapter number to process: "))
                    
            # Extract chapter sections
            with pdfplumber.open(pdf_path) as pdf:
                sections = extract_chapter_sections(pdf, structured_toc, page_offset, chapter)
            
            handler = ChatGPTHandler()
            
            # Get the first value of the first key in sections
            first_section_content = next(iter(sections.values()))
            
            questions = handler.generate_questions(first_section_content)
            
            # Convert Questions object to a dictionary
            questions_dict = questions.dict()
            
            # Save questions to a JSON file
            questions_file = os.path.join(OUTPUT_DIR, f"{book}_Chapter{chapter}_questions.json")
            with open(questions_file, 'w', encoding='utf-8') as f:
                json.dump(questions_dict, f, ensure_ascii=False, indent=2)
            
            print(f"Generated questions for Chapter {chapter} saved to {questions_file}")

        except Exception as e:
            print(f"An error occurred while processing {book}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
