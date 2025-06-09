
# PDF Financial Extractor Service

External Python microservice for robust PDF financial data extraction using pdfplumber and OCR.

## Features

- **Robust PDF text extraction** using pdfplumber
- **OCR fallback** using pytesseract for scanned PDFs
- **Swedish financial terminology** parsing
- **Table extraction** for structured data
- **CORS enabled** for frontend integration
- **Health monitoring** and logging
- **Docker containerized** for easy deployment

## API Endpoints

### POST /extract
Upload a PDF and extract financial data.

**Request:**
- File: PDF file (max 10MB)

**Response:**
```json
{
  "resultatrakning": {
    "omsättning": 1264637,
    "rörelseresultat": 310814,
    "resultat_före_skatt": 307493,
    "räntor": -3321
  },
  "balansrakning": {
    "likvida_medel": 306829,
    "kundfordringar": 591505,
    "leverantörsskulder": 26726,
    "eget_kapital": -237349,
    "långfristiga_skulder": 628347
  },
  "confidence": "high",
  "extracted_fields": 8,
  "extraction_method": "pdfplumber",
  "filename": "report.pdf",
  "success": true
}
```

### GET /health
Health check endpoint for monitoring.

## Deployment

### Local Development
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Docker
```bash
docker build -t pdf-extractor .
docker run -p 8000:8000 pdf-extractor
```

### Production (Render/Railway)
1. Push this directory to GitHub
2. Connect to Render/Railway
3. Select Dockerfile deployment
4. Set PORT environment variable if needed
5. Deploy

## Environment Variables

- `PORT`: Server port (default: 8000)

## Swedish Financial Terms Supported

**Resultaträkning:**
- Omsättning/Nettoomsättning/Försäljning
- Rörelseresultat/EBIT
- Resultat före skatt/EBT
- Räntekostnader/Finansiella kostnader

**Balansräkning:**
- Likvida medel/Bank/Kassa
- Kundfordringar/Fordringar
- Leverantörsskulder
- Eget kapital
- Långfristiga skulder/Banklån
