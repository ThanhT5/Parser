import pdfplumber
import logging
from typing import Dict
from .toc_detector import find_toc_pages
from .content_extractor import extract_chapter_sections
from .page_analyzer import find_page_offset
from src.exceptions.pdf_exceptions import PDFExtractionError, TOCNotFoundError
from src.ai_handler import ChatGPTHandler


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DEFAULT_MAX_TOKENS = 75000


def parse_table_of_contents(pdf, toc_pages) -> str:
    '''
    Extract raw content from TOC pages and prepare it for ChatGPT processing.
    Assumes the TOC is continuous. (Not true for some books, but it's a good enough approximation.)
    Returns the combined TOC content as a string.
    '''
    if not toc_pages:
        raise TOCNotFoundError("No table of contents found in the document")
       
    # Using list comprehension - more efficient than building string piece by piece
    page_contents = [
        f"\n--- Page {page_num + 1} ---\n{pdf.pages[page_num].extract_text().strip()}"
        for page_num in toc_pages
        if pdf.pages[page_num].extract_text().strip()  # Skip truly empty pages
    ]
       
    return '\n'.join(page_contents).strip()




def extract_chapter(pdf_path: str, desired_chapter: int, max_tokens: int = DEFAULT_MAX_TOKENS) -> Dict[str, str]:
    """
    Extract a specific chapter from the PDF.


    Args:
        pdf_path: Path to the PDF file
        desired_chapter: The chapter number to extract
        max_tokens: Maximum number of tokens per section


    Returns:
        A dictionary mapping section numbers to their content
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Find TOC pages and parse TOC content
            toc_pages = find_toc_pages(pdf)
            if not toc_pages:
                raise TOCNotFoundError("No table of contents found in the document")
               
            last_toc_page = max(toc_pages)
            toc_content = parse_table_of_contents(pdf)


            # Process TOC with ChatGPT
            handler = ChatGPTHandler()
            structured_toc = handler.process_toc(toc_content)


            # Find page offset
            page_offset = find_page_offset(pdf, structured_toc.model_dump(), last_toc_page)


            # Extract chapter sections
            sections = extract_chapter_sections(
                pdf,
                structured_toc.model_dump(),
                page_offset,
                desired_chapter,
                max_tokens
            )


            return sections
           
    except Exception as e:
        logger.error(f"Error extracting chapter: {str(e)}")
        raise PDFExtractionError(f"Failed to extract chapter: {str(e)}")

