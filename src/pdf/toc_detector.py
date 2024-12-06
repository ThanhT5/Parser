import re
from typing import List
from statistics import mode


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
    "brief contents", "contents at a glance"  # Terms to skip when searching for TOC
}


def find_toc_pages(pdf) -> List[int]:
    '''
    Main TOC detection function that uses a cascading approach with dynamic measurements.
    Tries the most reliable method first (columnar analysis),
    falls back to other methods if results are unreliable.
    '''
    # Get page dimensions for relative measurements
    page_width = float(pdf.pages[0].mediabox[2])
    min_title_page_distance = page_width * 0.15  # 15% of page width    
    # Enhanced patterns for TOC entries
    toc_patterns = [
        r'^(chapter|summary|conclusion|introduction|\d+\.|appendix\s+[a-z]|[ivxlcdm]+\.)',  # Standard chapters, summary, introduction, numbers, appendices, roman numerals
        r'^\d+\.\d+',  # Chapter sections (e.g., 1.1, 2.3, 10.4)
        r'^[A-Z][\.\s]',  # Single letter sections
        r'^(part|section|unit)\s+[a-z0-9]',  # Other common section markers
        r'^[\u0400-\u04FF]+',  # Support for non-Latin scripts (e.g., Cyrillic)
    ]


    # First check if TOC exists in first 20 pages
    toc_start_found = False
    for i in range(min(20, len(pdf.pages))):
        page = pdf.pages[i]
        text = page.extract_text().lower()
        if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):
            if not any(term in text for term in TOC_SKIP_TERMS):
                # Verify it's a TOC by checking for patterns and page numbers
                words = page.extract_words()
                for j, word in enumerate(words[:-1]):
                    if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                        next_words = []
                        k = j + 1
                        while len(next_words) < 10 and k < len(words):
                            if words[k]['text'] != '.':
                                next_words.append(words[k])
                            k += 1
                        if any(w['text'].isdigit() and
                              float(w['x0']) - float(word['x0']) > min_title_page_distance
                              for w in next_words):
                            toc_start_found = True
                            break
                if toc_start_found:
                    print(f"TOC start at page {i}")
                    break
   
    if not toc_start_found:
        print("Error: No TOC found within the first 20 pages.")
        return []
   
    # Try enhanced analysis first (most reliable for structured TOCs)
    toc_pages = find_toc_pages_3(pdf)
    if toc_pages:
        # Validate the result with enhanced patterns
        valid_entries = 0
        for page_num in toc_pages:
            page = pdf.pages[page_num]
            words = page.extract_words()
            for j, word in enumerate(words[:-1]):
                if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                    next_words = []
                    k = j + 1
                    while len(next_words) < 10 and k < len(words):
                        if words[k]['text'] != '.':
                            next_words.append(words[k])
                        k += 1
                    if any(w['text'].isdigit() and
                          float(w['x0']) - float(word['x0']) > min_title_page_distance
                          for w in next_words):
                        valid_entries += 1
                        break
       
        if valid_entries >= len(toc_pages) // 2:  # At least half the pages should have valid entries
            print(f"TOC found using enhanced analysis: {toc_pages}")
            return toc_pages
       
    # If enhanced method failed or gave suspicious results,
    # try columnar method
    toc_pages = find_toc_pages_2(pdf)
    if toc_pages:
        # Validate the result with enhanced patterns
        valid_entries = 0
        for page_num in toc_pages:
            page = pdf.pages[page_num]
            words = page.extract_words()
            for j, word in enumerate(words[:-1]):
                if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                    next_words = []
                    k = j + 1
                    while len(next_words) < 10 and k < len(words):
                        if words[k]['text'] != '.':
                            next_words.append(words[k])
                        k += 1
                    if any(w['text'].isdigit() and
                          float(w['x0']) - float(word['x0']) > min_title_page_distance
                          for w in next_words):
                        valid_entries += 1
                        break
       
        if valid_entries >= len(toc_pages) // 2:  # At least half the pages should have valid entries
            print(f"TOC found using columnar analysis: {toc_pages}")
            return toc_pages
   
    # If columnar method failed or gave suspicious results,
    # try numeric density method
    toc_pages = find_toc_pages_1(pdf)
    if toc_pages:
        # Validate with enhanced patterns
        valid_entries = 0
        for page_num in toc_pages:
            page = pdf.pages[page_num]
            words = page.extract_words()
            for j, word in enumerate(words[:-1]):
                if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                    next_words = []
                    k = j + 1
                    while len(next_words) < 10 and k < len(words):
                        if words[k]['text'] != '.':
                            next_words.append(words[k])
                        k += 1
                    if any(w['text'].isdigit() and
                          float(w['x0']) - float(word['x0']) > min_title_page_distance
                          for w in next_words):
                        valid_entries += 1
                        break
       
        if valid_entries >= len(toc_pages) // 2:
            print(f"TOC found using numeric density analysis: {toc_pages}")
            return toc_pages
   
    # If both methods failed or gave suspicious results,
    # fall back to original method with enhanced patterns
    return find_toc_pages_original(pdf)


def find_toc_pages_original(pdf) -> List[int]:
    '''
    Original TOC detection method.
    Used as a fallback when other methods fail.
    '''
    toc_pages = set()
    toc_started = False
   
    for i, page in enumerate(pdf.pages):
        text = page.extract_text().lower()
        words = page.extract_words()
       
        # Check for TOC start indicators
        if not toc_started:
            if any(term in text for term in TOC_SKIP_TERMS):
                continue
            if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):
                # Check for '1' or 'Chapter 1' as potential start of TOC
                for j, word in enumerate(words):
                    if word['text'] == '1' or (word['text'].lower() == 'chapter' and j+1 < len(words) and words[j+1]['text'] == '1'):
                        # Verify it's likely a TOC entry (check for page number)
                        if any(w['text'].isdigit() for w in words[j+1:j+10]):
                            toc_started = True
                            toc_pages.add(i)
                            break
       
        # If TOC has started, keep adding pages until we find an end indicator
        if toc_started:
            if any(term in text for term in TOC_END_TERMS):
                toc_pages.add(i)
                break
            toc_pages.add(i)
       
        # Limit to first 20 pages
        if i >= 20:
            print("Error: TOC not found within the first 20 pages.")
            return list(toc_pages)
   
    return list(toc_pages)


def find_toc_pages_1(pdf) -> List[int]:
    '''
    Find TOC pages using numeric density and layout analysis.
    Returns a list of page numbers where the TOC is found.
    '''
    toc_pages = set()
    toc_started = False
    prev_numeric_density = 0
   
    for i, page in enumerate(pdf.pages):
        text = page.extract_text().lower()
        words = page.extract_words()
       
        # Skip if page is empty
        if not words:
            continue
           
        # Calculate numeric density (ratio of numbers to total words)
        numeric_words = sum(1 for word in words if any(c.isdigit() for c in word['text']) and word['text'] not in {'.', ','})
        numeric_density = numeric_words / len(words) if words else 0
        # Check for TOC start
        if not toc_started:
            if any(term in text for term in TOC_SKIP_TERMS):
                continue
            if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):
                # Verify it's a TOC by checking numeric density
                if numeric_density > 0.08:  # At least 15% of words contain numbers
                    print(f"Numeric density: {numeric_density}, page: {i + 1}")
                    toc_started = True
                    toc_pages.add(i)
                    prev_numeric_density = numeric_density
       
        # If TOC has started, analyze layout and numeric density
        if toc_started:
            # Check for significant drop in numeric density (potential end of TOC)
            if numeric_density < prev_numeric_density * 0.5 and numeric_density < 0.1:
                # Verify it's not just a page break by checking next page if available
                if i + 1 < len(pdf.pages):
                    next_page = pdf.pages[i + 1]
                    next_words = next_page.extract_words()
                    next_numeric_density = sum(1 for word in next_words if any(c.isdigit() for c in word['text'])) / len(next_words) if next_words else 0
                    if next_numeric_density < 0.1:  # Confirm end of TOC
                        break
           
            # Check for transition to paragraph-style text
            if words:
                # Calculate average vertical spacing between words
                sorted_words = sorted(words, key=lambda w: w['top'])
                spacings = [sorted_words[i+1]['top'] - sorted_words[i]['bottom']
                          for i in range(len(sorted_words)-1)]
                avg_spacing = sum(spacings) / len(spacings) if spacings else 0
               
                # If spacing becomes more uniform (paragraph-style), it might be the end of TOC
                spacing_variance = sum((s - avg_spacing) ** 2 for s in spacings) / len(spacings) if spacings else float('inf')
                if spacing_variance < 5 and numeric_density < 0.15:  # Low variance indicates uniform text
                    break
           
            toc_pages.add(i)
            prev_numeric_density = numeric_density
       
        # Limit to first 30 pages
        if i >= 30:
            print("Error: TOC not found within the first 30 pages.")
            return list(toc_pages)
   
    return list(toc_pages)


def find_toc_pages_2(pdf) -> List[int]:
    '''
    Find TOC pages using columnar analysis and pattern matching.
    Returns a list of page numbers where the TOC is found.
    '''
    toc_pages = set()
    toc_started = False
    column_x_coords = None
   
    for i, page in enumerate(pdf.pages):
        text = page.extract_text().lower()
        words = page.extract_words()
       
        # Skip if page is empty
        if not words:
            continue
       
        # Check for TOC start
        if not toc_started:
            if any(term in text for term in TOC_SKIP_TERMS):
                continue
            if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):
                # Look for potential TOC pattern (title followed by page number)
                for j, word in enumerate(words[:-1]):
                    if re.match(r'^(chapter|\d+\.)', word['text'].lower()):
                        # Check for page number at the end of line or in right column
                        next_words = []
                        k = j + 1
                        while len(next_words) < 10 and k < len(words):
                            if words[k]['text'] != '.':
                                next_words.append(words[k])
                            k += 1
                        if any(w['text'].isdigit() and float(w['x0']) > float(word['x0']) + 100 for w in next_words):
                            toc_started = True
                            toc_pages.add(i)
                           
                            # Identify column structure
                            page_numbers = [w for w in words if w['text'].isdigit()]
                            if page_numbers:
                                x_coords = [float(w['x0']) for w in page_numbers]
                                # Group x-coordinates that are close together
                                x_clusters = []
                                current_cluster = [x_coords[0]]
                                for x in x_coords[1:]:
                                    if abs(x - current_cluster[-1]) < 20:
                                        current_cluster.append(x)
                                    else:
                                        if len(current_cluster) > 1:
                                            x_clusters.append(mode(current_cluster))
                                        current_cluster = [x]
                                if len(current_cluster) > 1:
                                    x_clusters.append(mode(current_cluster))
                                if x_clusters:
                                    column_x_coords = x_clusters
                            break
       
        # If TOC has started, verify page follows the same structure
        if toc_started:
            # Check for consistent column structure
            if column_x_coords:
                page_numbers = [w for w in words if w['text'].isdigit()]
                if page_numbers:
                    current_x_coords = [float(w['x0']) for w in page_numbers]
                    matches_structure = any(
                        any(abs(x - col_x) < 20 for col_x in column_x_coords)
                        for x in current_x_coords
                    )
                    if not matches_structure:
                        # Verify next page before concluding TOC end
                        if i + 1 < len(pdf.pages):
                            next_page = pdf.pages[i + 1]
                            next_words = next_page.extract_words()
                            next_numbers = [w for w in next_words if w['text'].isdigit()]
                            if not any(
                                any(abs(float(w['x0']) - col_x) < 20 for col_x in column_x_coords)
                                for w in next_numbers
                            ):
                                break
                        else:
                            break
           
            # Check for TOC entry pattern
            entries_found = 0
            for j, word in enumerate(words[:-1]):
                if re.match(r'^(chapter|\d+\.)', word['text'].lower()):
                    next_words = []
                    k = j + 1
                    while len(next_words) < 10 and k < len(words):
                        if words[k]['text'] != '.':
                            next_words.append(words[k])
                        k += 1
                    if any(w['text'].isdigit() and float(w['x0']) > float(word['x0']) + 100 for w in next_words):
                        entries_found += 1
           
            # If we find very few TOC-like entries, it might be the end
            if entries_found < 2 and i > min(toc_pages):
                # Verify with next page
                if i + 1 < len(pdf.pages):
                    next_page = pdf.pages[i + 1]
                    next_text = next_page.extract_text().lower()
                    if any(term in next_text for term in TOC_END_TERMS):
                        break
                else:
                    break
           
            toc_pages.add(i)
       
        # Limit to first 40 pages
        if i >= 40:
            print("Error: TOC not found within the first 40 pages.")
            return list(toc_pages)
   
    return list(toc_pages)


def find_toc_pages_3(pdf) -> List[int]:
    '''
    Enhanced TOC detection using dynamic measurements and improved pattern matching.
    Handles various chapter formats and adapts to different page layouts.
    '''
    toc_pages = set()
    toc_started = False
    column_x_coords = None
   
    # Get page dimensions for relative measurements
    page_width = float(pdf.pages[0].mediabox[2])
    min_title_page_distance = page_width * 0.15  # 15% of page width
    column_tolerance = page_width * 0.05  # 5% of page width
    # print(f"Column tolerance: {column_tolerance}")
   
    # Enhanced patterns for TOC entries
    toc_patterns = [
        r'^(chapter|summary|conclusion|introduction|\d+\.|appendix\s+[a-z]|[ivxlcdm]+\.)',  # Standard chapters, summary, introduction, numbers, appendices, roman numerals
        r'^\d+\.\d+',  # Chapter sections (e.g., 1.1, 2.3, 10.4)
        r'^[A-Z][\.\s]',  # Single letter sections
        r'^(part|section|unit)\s+[a-z0-9]',  # Other common section markers
        r'^[\u0400-\u04FF]+',  # Support for non-Latin scripts (e.g., Cyrillic)
    ]
   
    for i, page in enumerate(pdf.pages):
        text = page.extract_text().lower()
        words = page.extract_words()
       
        if not words:
            continue
       
        # Check for TOC start
        if not toc_started:
            if any(term in text for term in TOC_SKIP_TERMS):
                continue
            if any(re.search(r'\b' + re.escape(term) + r'\b', text) for term in TOC_START_TERMS):
                # Look for TOC pattern with dynamic distance check
                for j, word in enumerate(words[:-1]):
                    if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                        # Check for page number with dynamic distance
                        next_words = []
                        k = j + 1
                        while len(next_words) < 10 and k < len(words):
                            if words[k]['text'] != '.':
                                next_words.append(words[k])
                            k += 1
                        if any(w['text'].isdigit() and
                              float(w['x0']) - float(word['x0']) > min_title_page_distance
                              for w in next_words):
                            toc_started = True
                            toc_pages.add(i)
                           
                            # Identify column structure with dynamic tolerance
                            page_numbers = [w for w in words if w['text'].isdigit()]
                            if page_numbers:
                                x_coords = [float(w['x0']) for w in page_numbers]
                                x_clusters = []
                                current_cluster = [x_coords[0]]
                               
                                for x in x_coords[1:]:
                                    if abs(x - current_cluster[-1]) < column_tolerance:
                                        current_cluster.append(x)
                                    else:
                                        if len(current_cluster) > 1:
                                            x_clusters.append(mode(current_cluster))
                                        current_cluster = [x]
                               
                                if len(current_cluster) > 1:
                                    x_clusters.append(mode(current_cluster))
                                if x_clusters:
                                    column_x_coords = x_clusters
                                    # print(f"Column x-coords: {column_x_coords}")
                            break
       
        # If TOC has started, verify page follows the same structure
        if toc_started:
            # digit_words = [word for word in words if word['text'].isdigit()]
            # for word in digit_words:
            #     print(f"Digit: {word['text']} | x0: {word['x0']:.2f}")
            # Check for consistent column structure with dynamic tolerance
            if column_x_coords:
                page_numbers = [w for w in words if w['text'].isdigit()]
                if page_numbers:
                    current_x_coords = [float(w['x0']) for w in page_numbers]
                    matches_structure = any(
                        any(abs(x - col_x) <= column_tolerance for col_x in column_x_coords)
                        for x in current_x_coords
                    )
                    if not matches_structure:
                        # Verify next page before concluding TOC end
                        if i + 1 < len(pdf.pages):
                            next_page = pdf.pages[i + 1]
                            next_words = next_page.extract_words()
                            next_numbers = [w for w in next_words if w['text'].isdigit()]
                            if not any(
                                any(abs(float(w['x0']) - col_x) < column_tolerance for col_x in column_x_coords)
                                for w in next_numbers
                            ):
                                break
                        else:
                            break
           
            # Check for TOC entry pattern with dynamic distance
            entries_found = 0
            page_numbers_found = 0  # Initialize a counter for page numbers
            for j, word in enumerate(words[:-1]):
                if any(re.match(pattern, word['text'].lower()) for pattern in toc_patterns):
                    next_words = []
                    k = j + 1
                    while len(next_words) < 10 and k < len(words):
                        if words[k]['text'] != '.':
                            next_words.append(words[k])
                        k += 1
                    if any(w['text'].isdigit() and
                          float(w['x0']) - float(word['x0']) > min_title_page_distance
                          for w in next_words):
                        entries_found += 1
            
            # Count the number of page numbers on the current page
            page_numbers_found = sum(1 for word in words if word['text'].isdigit())
            # If we find very few TOC-like entries or page numbers, it might be the end
            if entries_found < 2 or page_numbers_found < 5 and i > min(toc_pages):
                print(f"Page {i} has less than 2 TOC-like entries or {page_numbers_found} page numbers")
                # Verify with next page
                if i + 1 < len(pdf.pages):
                    next_page = pdf.pages[i + 1]
                    next_text = next_page.extract_text().lower()
                    if any(term in next_text for term in TOC_END_TERMS):
                        toc_pages.add(i + 1)
                        break
                    if page_numbers_found < 5:
                        break
                else:
                    break
            toc_pages.add(i)
       
        # Limit to first 30 pages
        if i >= 30:
            print("Error: TOC not found within the first 30 pages.")
            return list(toc_pages)
   
    return list(toc_pages)