#!/usr/bin/env python

import fitz  # PyMuPDF
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def pdf_to_docx_fidelidade(pdf_file, docx_path):
    # Abre o documento PDF
    pdf_document = fitz.open(pdf_file)
    
    # Cria um novo documento DOCX
    docx_document = Document()
    
    # Itera sobre cada página do PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")
        
        # Adiciona o texto da página ao DOCX
        paragraph = docx_document.add_paragraph(text)
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    
    # Salva o documento DOCX
    docx_document.save(docx_path)

if __name__ == "__main__":
    pdf_file = "path/to/your/input.pdf"
    docx_file = "path/to/your/output.docx"
    pdf_to_docx_fidelidade(pdf_file, docx_file)
