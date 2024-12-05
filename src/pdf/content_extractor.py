import logging
import time
from typing import List, Dict, Tuple
import tiktoken
from src.utils.resource_monitor import ResourceMonitor
from src.exceptions.pdf_exceptions import PDFExtractionError


logger = logging.getLogger(__name__)


def distribute_questions(extracted_sections: Dict[str, str], total_questions: int = 15) -> Dict[str, int]:
    """
    Calculate how many questions each section should get based on content length.
   
    Args:
        extracted_sections: Dictionary mapping section numbers to their content
        total_questions: Total number of questions desired for the chapter
       
    Returns:
        Dictionary mapping section numbers to their allocated question count
    """
    # Calculate total content length
    total_chars = sum(len(content) for content in extracted_sections.values())
   
    # Initial distribution based on content length
    questions_per_section = {}
    remaining_questions = total_questions
   
    # Ensure at least one question per section
    min_questions = 1
    reserved_questions = len(extracted_sections) * min_questions
   
    if reserved_questions > total_questions:
        # If we can't give each section one question, distribute evenly
        questions_per_section = {
            section: total_questions // len(extracted_sections)
            for section in extracted_sections
        }
        return questions_per_section
   
    # Distribute remaining questions proportionally
    remaining_questions -= reserved_questions
   
    for section, content in extracted_sections.items():
        # Start with minimum questions
        section_questions = min_questions
       
        if total_chars > 0:
            # Add proportional share of remaining questions
            proportion = len(content) / total_chars
            additional_questions = int(proportion * remaining_questions)
            section_questions += additional_questions
       
        questions_per_section[section] = section_questions
   
    # Distribute any remaining questions to longest sections
    actual_total = sum(questions_per_section.values())
    remaining = total_questions - actual_total
   
    if remaining > 0:
        sections_by_length = sorted(
            extracted_sections.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
       
        for section, _ in sections_by_length:
            if remaining <= 0:
                break
            questions_per_section[section] += 1
            remaining -= 1
   
    return questions_per_section


def extract_chapter_sections(
    pdf,
    structured_toc: dict,
    page_offset: int,
    desired_chapter: int,
    max_tokens: int = 75000,
    batch_size: int = 3,  # Process pages in small batches
    total_questions: int = 15
) -> Tuple[Dict[str, str], Dict[str, int]]:
    """
    Extract chapter sections and calculate question distribution.
   
    Args:
        pdf: PDF object from pdfplumber
        structured_toc: Structured table of contents
        page_offset: Page offset
        desired_chapter: Chapter number to extract
        max_tokens: Maximum tokens per section
        batch_size: Number of pages to process in each batch
        total_questions: Total number of questions to distribute
   
    Returns:
        Tuple containing:
        - Dictionary mapping section numbers to content
        - Dictionary mapping section numbers to question counts
    """
    start_time = time.time()
   
    # Constants for optimization
    MAX_PAGES_PER_SECTION = 50
    CHARS_PER_TOKEN = 4
    MAX_CHARS = max_tokens * CHARS_PER_TOKEN
   
    # Initialize resource monitor
    monitor = ResourceMonitor(cpu_threshold=70, memory_threshold=80)
   
    def log_progress(message: str, start_time: float) -> None:
        """Log progress with elapsed time"""
        elapsed = time.time() - start_time
        logger.info(f"{message} (Elapsed: {elapsed:.2f}s)")


    def process_page_batch(pages: List[int], monitor: ResourceMonitor) -> List[str]:
        """Process a batch of pages with resource monitoring and error handling"""
        batch_texts = []
        for page_num in pages:
            try:
                with monitor.throttle_if_needed(check_interval=1):
                    if page_num >= len(pdf.pages):
                        continue
                   
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    if text and text.strip():
                        # Basic text cleaning
                        text = ' '.join(text.split())  # Normalize whitespace
                        batch_texts.append(text)
                   
                    # Explicitly clear page object from memory
                    page.flush_cache()
                   
            except Exception as e:
                logger.warning(f"Error processing page {page_num}: {str(e)}")
                continue
               
        return batch_texts


    try:
        # Find chapter and validate
        chapter = next((entry for entry in structured_toc['entries']
                       if entry['level'] == 0 and entry['number'] == str(desired_chapter)), None)
        if not chapter:
            raise PDFExtractionError(f"Chapter {desired_chapter} not found in TOC")


        log_progress("Found chapter in TOC", start_time)


        # Get chapter sections (does not include summary, etc)
        chapter_sections = [entry for entry in structured_toc['entries']
                          if entry['level'] == 1 and entry['number'].startswith(f"{desired_chapter}.")]
        if not chapter_sections:
            chapter_sections = [chapter]


        # Find next chapter for hard limit
        next_chapter = next((entry for entry in structured_toc['entries']
                           if entry['level'] == 0 and int(entry['number']) == desired_chapter + 1), None)
        pdf_limit = (next_chapter['page'] + page_offset if next_chapter
                    else min(chapter['page'] + page_offset + MAX_PAGES_PER_SECTION, len(pdf.pages)))


        extracted_sections = {}
        enc = tiktoken.encoding_for_model("gpt-4")


        # Process sections
        for i, section in enumerate(chapter_sections):
            section_start_time = time.time()
           
            start_page = section['page'] + page_offset
            if i + 1 < len(chapter_sections):
                end_page = min(chapter_sections[i + 1]['page'] + page_offset, pdf_limit)
            else:
                end_page = min(start_page + MAX_PAGES_PER_SECTION, pdf_limit)


            # Process pages in batches
            section_texts = []
            for batch_start in range(start_page, end_page, batch_size):
                batch_end = min(batch_start + batch_size, end_page)
                batch_pages = list(range(batch_start, batch_end))
               
                with monitor.throttle_if_needed():
                    batch_texts = process_page_batch(batch_pages, monitor)
                    section_texts.extend(batch_texts)


            if not section_texts:
                logger.warning(f"No content extracted for section {section['number']}")
                continue


            # Join text and check size
            section_content = '\n'.join(section_texts)
            content_length = len(section_content)


            # Log section processing time
            log_progress(f"Processed section {section['number']}", section_start_time)


            # Handle content splitting if necessary
            if content_length > MAX_CHARS:
                with monitor.throttle_if_needed():
                    tokens = enc.encode(section_content)
                    if len(tokens) > max_tokens:
                        # Split into parts based on character count
                        avg_chars_per_part = content_length // ((len(tokens) // max_tokens) + 1)
                        parts = []
                        current_part = []
                        current_length = 0


                        for paragraph in section_content.split('\n'):
                            current_length += len(paragraph)
                            if current_length > avg_chars_per_part and current_part:
                                parts.append('\n'.join(current_part))
                                current_part = [paragraph]
                                current_length = len(paragraph)
                            else:
                                current_part.append(paragraph)


                        if current_part:
                            parts.append('\n'.join(current_part))


                        # Store split parts
                        for j, part in enumerate(parts, 1):
                            section_number = (f"{section['number']}.{j}"
                                           if section['level'] == 1
                                           else f"{desired_chapter}.{j}")
                            extracted_sections[section_number] = part
                        continue


            # Store unsplit content
            section_number = (section['number']
                            if section['level'] == 1
                            else str(desired_chapter))
            extracted_sections[section_number] = section_content


        total_time = time.time() - start_time
        logger.info(f"Complete chapter extraction took {total_time:.2f} seconds")


        # After successful extraction, calculate question distribution
        question_distribution = distribute_questions(extracted_sections, total_questions)
       
        return extracted_sections, question_distribution


    except Exception as e:
        logger.error(f"Error during chapter extraction: {str(e)}")
        raise PDFExtractionError(f"Failed to extract chapter {desired_chapter}: {str(e)}")