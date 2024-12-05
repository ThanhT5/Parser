class PDFExtractionError(Exception):
    """Custom exception for PDF extraction errors"""
    pass


class TOCNotFoundError(PDFExtractionError):
    """Exception raised when Table of Contents cannot be found"""
    pass


class ChapterNotFoundError(PDFExtractionError):
    """Exception raised when a specific chapter cannot be found"""
    pass


class PageOffsetError(PDFExtractionError):
    """Exception raised when page offset cannot be determined"""
    pass


class ContentExtractionError(PDFExtractionError):
    """Exception raised when content extraction fails"""
    pass