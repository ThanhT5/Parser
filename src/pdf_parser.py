import pdfplumber  # Import pdfplumber for handling PDF files
import re  # Import re for regular expression matching
import os  # Import os for file path operations
from typing import List, Dict  # Import necessary types for type hinting
from src.ai_handler import ChatGPTHandler  # Import the ChatGPTHandler for processing TOC
import tiktoken  # For token counting
from src.utils.resource_monitor import ResourceMonitor  # Import the ResourceMonitor for throttling
# Define the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define input and output directories
INPUT_DIR = os.path.join(BASE_DIR, 'data')  # Directory where input PDF files are located
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')  # Directory where output JSON files will be saved

# Set of terms that might indicate a table of contents (TOC)
TOC_START_TERMS = {
    'content', 'contents', 'ontent', 'ontents', 'table of contents', 
    'table of chapters', 'chapter index', 'chapter list'
}  # 'ontents' is included to account for potential OCR errors
TOC_END_TERMS = {
    "index", "answer key", "glossary", "appendix", "exercise solutions",
    "references", "credits",
}
TOC_SKIP_TERMS = {
    "brief contents"  # Terms to skip when searching for TOC
}

def find_toc_pages(pdf) -> List[int]:
    '''
    Find the pages that contain the table of contents (TOC).
    Returns a list of page numbers where the TOC is found.
    '''
    toc_pages = set()  # Set to store unique TOC page numbers
    toc_started = False  # Flag to indicate if TOC has started
    
    for i, page in enumerate(pdf.pages):  # Iterate through each page in the PDF
        text = page.extract_text().lower()  # Extract and lower case the text
        words = page.extract_words()  # Extract words from the page
        
        # Check for TOC start indicators
        if not toc_started:
            if any(term in text for term in TOC_SKIP_TERMS):  # Check for TOC skip terms
                continue  # Skip the page if it contains a skip term
            if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):  # Check for TOC start terms
                # Check for '1' or 'Chapter 1' as potential start of TOC
                for j, word in enumerate(words):
                    if word['text'] == '1' or (word['text'].lower() == 'chapter' and j+1 < len(words) and words[j+1]['text'] == '1'):
                        # Verify it's likely a TOC entry (check for page number)
                        if any(w['text'].isdigit() for w in words[j+1:j+10]):  # Check next few words for a page number
                            toc_started = True  # Set flag to indicate TOC has started
                            toc_pages.add(i)  # Add current page to TOC pages
                            break  # Exit the loop once TOC is found
        
        # If TOC has started, keep adding pages until we find an end indicator
        if toc_started:
            if any(term in text for term in TOC_END_TERMS):  # Check for TOC end terms
                toc_pages.add(i)  # Add current page to TOC pages
                break  # Stop when we find an end-of-TOC term
            toc_pages.add(i)  # Add current page to TOC pages
        
        # Limit to first 50 pages to avoid long processing
        if i >= 50:  
            print("Error: TOC not found within the first 50 pages.")  # Log error if TOC not found
            return list(toc_pages)  # Return the pages found so far as a list
        
    return list(toc_pages)  # Return the list of TOC pages found

def parse_table_of_contents(pdf) -> str:
    '''
    Extract raw content from TOC pages and prepare it for ChatGPT processing.
    Assumes the TOC is continuous. (Not true for some books, but it's a good enough approximation.)
    Returns the combined TOC content as a string.
    '''
    # Find the pages that contain the table of contents (TOC)
    toc_pages = find_toc_pages(pdf)  # Call the function to get TOC pages
    combined_content = ""  # Initialize an empty string to hold combined TOC content

    # Iterate through each page number found in the TOC
    for page_num in toc_pages:
        page = pdf.pages[page_num]  # Get the page object from the PDF
        content = page.extract_text()  # Extract text from the page
        # Append the extracted content to combined_content with page number header
        combined_content += f"\n--- Page {page_num + 1} ---\n{content}\n"

    return combined_content.strip()  # Return the combined content without leading/trailing whitespace

def find_page_offset(pdf, structured_toc: dict, last_toc_page: int) -> int:
    """
    Find the offset between PDF page numbers and book page numbers by searching for page numbers
    and verifying with the first chapter and optionally its first section.
    """
    if not structured_toc.get('entries'):
        raise ValueError("Structured TOC is empty")  # Raise error if TOC is empty

    # Find the first chapter and its first section (if it exists)
    first_chapter = next((entry for entry in structured_toc['entries'] if entry['level'] == 0), None)
    first_section = next((entry for entry in structured_toc['entries'] if entry['level'] == 1 and entry['number'].startswith(f"{first_chapter['number']}.")), None)

    if not first_chapter:
        raise ValueError("Could not find first chapter in TOC")  # Raise error if no chapter found

    chapter_page = first_chapter['page']  # Get the page number of the first chapter
    chapter_title = first_chapter['title']  # Get the title of the first chapter
    section_page = first_section['page'] if first_section else None  # Get the page number of the first section
    section_title = first_section['title'] if first_section else None  # Get the title of the first section

    def extract_page_number(text):
        # Extract page number from top or bottom of the page
        lines = text.split('\n')  # Split text into lines
        first_line = lines[0].strip()  # Get the first line
        last_line = lines[-1].strip()  # Get the last line
        
        # Check both the first and last lines for page numbers
        for line in [first_line, last_line]:
            numbers = re.findall(r'\b\d+\b', line)  # Find all numbers in the line
            if numbers:
                return int(numbers[0])  # Return the first found number as the page number
        return None  # Return None if no page number is found

    # Iterate through the pages after the last TOC page to find the offset
    for pdf_page_number in range(last_toc_page + 1, len(pdf.pages)):
        page = pdf.pages[pdf_page_number]  # Get the current page
        text = page.extract_text()  # Extract text from the page
        
        page_number = extract_page_number(text)  # Extract the page number
        print(page_number)  # Print the extracted page number for debugging
        if page_number is None:
            continue  # Skip pages without visible page numbers

        # Check for the chapter page
        if page_number == chapter_page:
            if re.search(re.escape(chapter_title), text, re.IGNORECASE):
                offset = pdf_page_number - chapter_page  # Calculate the offset
                print(f"First chapter '{chapter_title}' found on page {pdf_page_number}, offset: {offset}")
                return offset  # Return the calculated offset

        # Check for the section page (if it exists)
        if section_page and page_number == section_page:
            if section_title and re.search(re.escape(section_title), text, re.IGNORECASE):
                offset = pdf_page_number - section_page  # Calculate the offset
                print(f"First section '{section_title}' found on page {pdf_page_number}, offset: {offset}")
                return offset  # Return the calculated offset

        # If we've passed the expected section page without finding it, break the loop
        if section_page and page_number > section_page:
            break

    # If we've reached this point, we couldn't find the chapter or section
    raise ValueError(f"Could not find consistent offset for first chapter (page {chapter_page}) or its first section (page {section_page})")

def extract_chapter_sections(pdf, structured_toc: dict, page_offset: int, desired_chapter: int, max_tokens: int = 75000, batch_size: int = 5) -> dict:
    """
    Extract and label sections for a given chapter number, splitting large sections if necessary.
    Includes resource monitoring and batch processing for efficient resource usage.
   
    Args:
        pdf: The PDF object
        structured_toc: The structured table of contents
        page_offset: The calculated page offset
        desired_chapter: The chapter number to extract
        max_tokens: Maximum number of tokens per section (default 75000)
        batch_size: Number of pages to process in each batch (default 5)
    Returns:
        A dictionary with section numbers as keys and their content as values
    """
    # Initialize resource monitor with conservative thresholds for t2.micro
    monitor = ResourceMonitor(cpu_threshold=70, memory_threshold=80)
   
    def process_text_batch(pages: List[int]) -> str:
        """Process a batch of pages with resource monitoring."""
        batch_content = ""
        for page_num in pages:
            with monitor.throttle_if_needed():
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    batch_content += page.extract_text()
                    # Release page object explicitly
                    page.flush_cache()
        return batch_content.strip()


    # Find the desired chapter in the TOC
    chapter = next((entry for entry in structured_toc['entries']
                   if entry['level'] == 0 and entry['number'] == str(desired_chapter)), None)
   
    if not chapter:
        raise ValueError(f"Chapter {desired_chapter} not found in the table of contents.")
   
    # Find all sections of the desired chapter
    chapter_sections = [entry for entry in structured_toc['entries']
                       if entry['level'] == 1 and entry['number'].startswith(f"{desired_chapter}.")]
   
    if not chapter_sections:
        chapter_sections = [chapter]
   
    extracted_sections = {}
    enc = tiktoken.encoding_for_model("gpt-4")  # or whichever model you're using


    # Process sections in batches
    for i, section in enumerate(chapter_sections):
        start_page = section['page'] + page_offset
        end_page = (chapter_sections[i+1]['page'] + page_offset
                   if i+1 < len(chapter_sections) else len(pdf.pages))
       
        section_content = ""
        # Process pages in batches
        for batch_start in range(start_page, end_page, batch_size):
            batch_end = min(batch_start + batch_size, end_page)
            batch_pages = list(range(batch_start, batch_end))
           
            with monitor.throttle_if_needed():
                batch_content = process_text_batch(batch_pages)
                section_content += batch_content


        # Process the section content
        with monitor.throttle_if_needed():
            tokens = enc.encode(section_content)
           
            if len(tokens) > max_tokens:
                # Split into smaller chunks if needed
                parts = []
                current_part = ""
                current_tokens = 0
               
                for paragraph in section_content.split('\n'):
                    paragraph_tokens = enc.encode(paragraph)
                    if current_tokens + len(paragraph_tokens) > max_tokens:
                        if current_part:
                            parts.append(current_part.strip())
                        current_part = paragraph
                        current_tokens = len(paragraph_tokens)
                    else:
                        current_part += "\n" + paragraph
                        current_tokens += len(paragraph_tokens)
               
                if current_part:
                    parts.append(current_part.strip())
               
                # Store the parts with appropriate section numbers
                for j, part in enumerate(parts, 1):
                    section_number = (f"{section['number']}.{j}"
                                   if section['level'] == 1
                                   else f"{desired_chapter}.{j}")
                    extracted_sections[section_number] = part
            else:
                # Store the entire section if it's within token limits
                section_number = (section['number']
                                if section['level'] == 1
                                else str(desired_chapter))
                extracted_sections[section_number] = section_content


    return extracted_sections

def analyze_pdf_and_generate_questions(pdf_path: str, desired_chapter: int, max_tokens: int = 75000) -> List[str]:
    """
    Analyze the PDF structure, extract chapter sections, and generate questions.

    :param pdf_path: Path to the PDF file
    :param desired_chapter: The chapter number to process
    :param max_tokens: Maximum number of tokens per section (default 75000)
    :return: A list of generated questions
    """
    with pdfplumber.open(pdf_path) as pdf:  # Open the PDF file
        # Find TOC pages and parse TOC content
        toc_pages = find_toc_pages(pdf)  # Get the pages containing the TOC
        last_toc_page = max(toc_pages) if toc_pages else 0  # Get the last TOC page
        toc_content = parse_table_of_contents(pdf)  # Extract TOC content

        # Process TOC with ChatGPT
        handler = ChatGPTHandler()  # Create an instance of ChatGPTHandler
        structured_toc = handler.process_toc(toc_content)  # Process the TOC content

        # Find page offset
        page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)  # Calculate page offset

        # Extract chapter sections
        sections = extract_chapter_sections(pdf, structured_toc.model_dump(), page_offset, desired_chapter, max_tokens)  # Extract sections for the desired chapter

        # Generate questions for each section
        all_questions = []  # List to hold all generated questions
        for section_number, content in sections.items():  # Iterate through each section
            questions = handler.generate_questions(content, section_number)  # Generate questions for the section
            all_questions.extend(questions)  # Add the generated questions to the list

    return all_questions  # Return the list of generated questions