import re
from typing import Dict


def find_page_offset(pdf, structured_toc: Dict, last_toc_page: int) -> int:
    """
    Find the offset between PDF page numbers and book page numbers.
    Returns the number that needs to be added to book page numbers to get PDF page numbers.
   
    Args:
        pdf: PDF document object
        structured_toc: Dictionary containing parsed TOC with entries
        last_toc_page: Last page number of the TOC
   
    Returns:
        int: Page number offset
   
    Raises:
        ValueError: If offset cannot be determined reliably
    """
    if not structured_toc.get('entries'):
        raise ValueError("Structured TOC is empty")


    # Find first chapter and section with better error handling
    chapters = [entry for entry in structured_toc['entries'] if entry['level'] == 0]
    if not chapters:
        raise ValueError("No chapters found in TOC")
   
    first_chapter = chapters[0]
    first_section = next(
        (entry for entry in structured_toc['entries']
         if entry['level'] == 1 and entry['number'].startswith(f"{first_chapter['number']}.")),
        None
    )


    def extract_page_numbers(text: str) -> list[int]:
        """Extract all potential page numbers from a page."""
        # Split into lines and clean
        lines = [line.strip() for line in text.split('\n')]
       
        # Focus on first/last 3 lines where page numbers typically appear
        candidate_lines = lines[:3] + lines[-3:]
       
        numbers = []
        for line in candidate_lines:
            # More robust number extraction
            matches = re.findall(r'(?<!\d)\d{1,4}(?!\d)', line)
            numbers.extend(int(match) for match in matches)
       
        return numbers


    def text_matches_title(text: str, title: str) -> bool:
        """Check if text contains the title, handling common OCR issues."""
        # Clean and normalize text for comparison
        clean_text = re.sub(r'\s+', ' ', text.lower().strip())
        clean_title = re.sub(r'\s+', ' ', title.lower().strip())
       
        # Try exact match first
        if clean_title in clean_text:
            return True
           
        # Try fuzzy match for OCR errors
        words = clean_title.split()
        return all(word in clean_text for word in words)


    # Search range with a safety margin
    search_range = range(
        max(last_toc_page + 1, 0),
        min(last_toc_page + 50, len(pdf.pages))  # Limit search range
    )


    potential_offsets = []
   
    for pdf_page_number in search_range:
        page = pdf.pages[pdf_page_number]
        text = page.extract_text()
        page_numbers = extract_page_numbers(text)
       
        for page_number in page_numbers:
            # Check chapter match
            if page_number == first_chapter['page']:
                if text_matches_title(text, first_chapter['title']):
                    offset = pdf_page_number - first_chapter['page']
                    potential_offsets.append((offset, 'chapter'))
           
            # Check section match if exists
            if first_section and page_number == first_section['page']:
                if text_matches_title(text, first_section['title']):
                    offset = pdf_page_number - first_section['page']
                    potential_offsets.append((offset, 'section'))


    # Analyze results
    if not potential_offsets:
        raise ValueError("Could not determine page offset")
       
    # If multiple matches found, prefer chapter match
    chapter_offsets = [offset for offset, source in potential_offsets if source == 'chapter']
    if chapter_offsets:
        return chapter_offsets[0]
       
    # Fall back to section match
    return potential_offsets[0][0]