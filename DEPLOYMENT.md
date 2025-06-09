
# PDF Extractor Service - Deployment Guide

## Quick Deploy på Render

### Steg 1: Förbered GitHub Repository
1. Skapa ett nytt GitHub repository (t.ex. `pdf-extractor-service`)
2. Ladda upp hela `python-pdf-extractor/` mappen till repositoryet
3. Säkerställ att `Dockerfile`, `requirements.txt` och `main.py` finns i root

### Steg 2: Deploy på Render
1. Gå till [render.com](https://render.com) och logga in
2. Klicka "New +" → "Web Service"
3. Anslut ditt GitHub repository
4. Välj `python-pdf-extractor` mappen
5. Konfigurera:
   - **Name**: `pdf-extractor-elliventures`
   - **Environment**: `Docker`
   - **Build Command**: (tom - Dockerfile används)
   - **Start Command**: (tom - CMD i Dockerfile används)
   - **Port**: `8000`

### Steg 3: Environment Variables
Sätt dessa environment variables i Render:
- `PORT`: `8000`

### Steg 4: Deploy
1. Klicka "Create Web Service"
2. Vänta på deployment (5-10 minuter första gången)
3. Din service blir tillgänglig på: `https://pdf-extractor-elliventures.onrender.com`

### Steg 5: Verifiera Deployment
Testa health endpoint:
```bash
curl https://pdf-extractor-elliventures.onrender.com/health
```

Förväntat svar:
```json
{"status": "healthy", "service": "pdf-extractor"}
```

## Alternativ: Railway Deploy

### Railway Steps
1. Gå till [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Välj ditt repository
4. Railway upptäcker automatiskt Dockerfile
5. Deploy sker automatiskt

## Alternativ: Fly.io Deploy

### Fly.io Steps
1. Installera Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. I `python-pdf-extractor/` mappen:
   ```bash
   fly launch --name pdf-extractor-elliventures
   fly deploy
   ```

## Environment Update i Frontend

Efter deployment, uppdatera frontend environment:

### För utveckling (.env.local om tillgängligt):
```bash
VITE_PDF_SERVICE_URL=https://pdf-extractor-elliventures.onrender.com
```

### För produktion:
Sätt environment variable i Lovable project settings eller deploy-plattformen.

## Monitoring & Logs

### Render Logs
- Gå till Render dashboard → din service → "Logs"
- Livemonitorering av FastAPI-anrop

### Test Full Integration
1. Gå till `/ai-finansieringscoachen` i Lovable-appen
2. Ladda upp test-PDFs
3. Kontrollera att external service anropas
4. Verifiera att data extraheras korrekt

## Troubleshooting

### Service ikke svarar
- Kontrollera Render service status
- Kolla logs för felmeddelanden
- Verifiera att port 8000 exponeras

### CORS-problem
- Kontrollera att `allow_origins=["*"]` är satt i `main.py`
- För produktion: specificera Lovable domain

### OCR-problem
- Tesseract installeras automatiskt i Docker
- Svenska språkpaket (`tesseract-ocr-swe`) inkluderat

## URL Update Checklist

✅ Deploy Python service på Render/Railway  
✅ Få live URL (t.ex. `https://pdf-extractor-elliventures.onrender.com`)  
✅ Testa `/health` endpoint  
✅ Uppdatera `PDF_SERVICE_URL` i environment  
✅ Testa full integration från Lovable frontend  
✅ Verifiera fallback till manuell inmatning fungerar  
