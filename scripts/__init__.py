"""
Ebook Pipeline & 1-bit Monochrome Optimization Suite
"""
from .convert_books import convert_document_to_epub, convert_scanned_pdf_to_epub, convert_digital_pdf_to_epub
from .fix_epub_covers import fix_epub_cover
from .clean_large_epubs import clean_epub_artifacts

__all__ = [
    'convert_document_to_epub',
    'convert_scanned_pdf_to_epub',
    'convert_digital_pdf_to_epub',
    'fix_epub_cover',
    'clean_epub_artifacts',
]
