
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import tempfile
import re
import os
from typing import Dict, Any, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Financial Extractor", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Lovable domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_number(val: str) -> Optional[int]:
    """Konvertera svenska siffror med tusentalsavgränsare och ev. mellanslag."""
    if not val:
        return None
    try:
        # Remove spaces, dots (thousand separators), handle negative numbers
        cleaned = val.replace(" ", "").replace(".", "").replace(",", ".")
        # Handle negative numbers in parentheses
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return None

def extract_text_with_pdfplumber(file_bytes: bytes) -> Optional[str]:
    """Extract text using pdfplumber - best for structured PDFs."""
    try:
        text = ""
        with pdfplumber.open(file_bytes) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                
                # Also try to extract tables
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text += " ".join([cell or "" for cell in row]) + "\n"
        
        return text.strip() if text.strip() else None
    except Exception as e:
        logger.error(f"pdfplumber extraction failed: {e}")
        return None

def fallback_ocr(file_bytes: bytes) -> Optional[str]:
    """OCR fallback for scanned PDFs using pytesseract."""
    try:
        images = convert_from_bytes(file_bytes, dpi=300)
        text = ""
        for img in images:
            page_text = pytesseract.image_to_string(img, lang='swe+eng')
            text += page_text + "\n"
        return text.strip() if text.strip() else None
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return None

def parse_financials(text: str) -> Dict[str, Any]:
    """Parse Swedish financial data from extracted text."""
    result = {
        "resultatrakning": {},
        "balansrakning": {},
        "confidence": "medium",
        "extracted_fields": 0
    }
    
    # Improved regex patterns for Swedish financial terms
    patterns = {
        # Income Statement (Resultaträkning)
        "omsättning": [
            r"(?:Netto)?oms[aä]ttning\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"F[oö]rs[aä]ljning\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"Int[aä]kter\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        "rörelseresultat": [
            r"R[oö]relseresultat\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"EBIT\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        "resultat_före_skatt": [
            r"Resultat f[oö]re skatt\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"EBT\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        "räntor": [
            r"R[aä]ntekostnader?\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"Finansiella kostnader\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        
        # Balance Sheet (Balansräkning)
        "likvida_medel": [
            r"Likvida medel\s*[:\-]?\s*([\d\s.,()]+)",
            r"Bank\s*[:\-]?\s*([\d\s.,()]+)",
            r"Kassa\s*[:\-]?\s*([\d\s.,()]+)"
        ],
        "kundfordringar": [
            r"Kundfordringar\s*[:\-]?\s*([\d\s.,()]+)",
            r"Fordringar\s*[:\-]?\s*([\d\s.,()]+)"
        ],
        "leverantörsskulder": [
            r"Leverant[oö]rsskulder\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"Skulder till leverant[oö]rer\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        "eget_kapital": [
            r"Eget kapital\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"Equity\s*[:\-]?\s*([\d\s.,\-()]+)"
        ],
        "långfristiga_skulder": [
            r"L[aå]ngfristiga skulder\s*[:\-]?\s*([\d\s.,\-()]+)",
            r"Banklån\s*[:\-]?\s*([\d\s.,\-()]+)"
        ]
    }
    
    fields_found = 0
    
    for field_name, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                val = clean_number(match.group(1))
                if val is not None:
                    if field_name in ["omsättning", "rörelseresultat", "resultat_före_skatt", "räntor"]:
                        result["resultatrakning"][field_name] = val
                    else:
                        result["balansrakning"][field_name] = val
                    fields_found += 1
                    break  # Use first match for each field
    
    result["extracted_fields"] = fields_found
    
    # Set confidence based on extracted fields
    if fields_found >= 7:
        result["confidence"] = "high"
    elif fields_found >= 4:
        result["confidence"] = "medium"
    else:
        result["confidence"] = "low"
    
    return result

@app.get("/")
async def root():
    return {"message": "PDF Financial Extractor API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pdf-extractor"}

@app.post("/extract")
async def extract_from_pdf(file: UploadFile = File(...)):
    """Extract financial data from uploaded PDF."""
    
    # Validate file type
    if not file.content_type or "pdf" not in file.content_type.lower():
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    try:
        logger.info(f"Processing PDF: {file.filename} ({file.size} bytes)")
        
        # Read file bytes
        file_bytes = await file.read()
        
        # Try pdfplumber first
        text = extract_text_with_pdfplumber(file_bytes)
        extraction_method = "pdfplumber"
        
        # Fallback to OCR if pdfplumber fails or returns minimal text
        if not text or len(text) < 50:
            logger.info("Falling back to OCR extraction...")
            text = fallback_ocr(file_bytes)
            extraction_method = "ocr"
        
        if not text:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract text from PDF. Please ensure the PDF contains readable text or try a different file."
            )
        
        # Parse financial data
        parsed_data = parse_financials(text)
        
        # Add metadata
        response = {
            **parsed_data,
            "filename": file.filename,
            "extraction_method": extraction_method,
            "text_length": len(text),
            "success": True
        }
        
        logger.info(f"Successfully extracted {parsed_data['extracted_fields']} fields with {parsed_data['confidence']} confidence")
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing PDF: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
