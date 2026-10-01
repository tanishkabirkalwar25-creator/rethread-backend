# RE-THREAD backend (deploy separately from the static frontend)
1. AI service: `cd ai_service && pip install -r requirements.txt` (install the `tesseract` binary), put fabric-trained
   `resnet50_fabric.keras`, `nasnet_fabric.keras`, `classes.json` in `MODEL_DIR`, run `gunicorn -b 0.0.0.0:5000 app:app`.
2. API: `npm install && AI_SERVICE_URL=https://<ai-service> ALLOWED_ORIGIN=https://<frontend> npm start` (host with HTTPS).
3. Frontend: create `config.js` next to the HTML: `window.RETHREAD_API_URL = "https://<api-host>";`
4. Verify: `GET <api>/api/health` -> 200 {"success":true,"status":"running"}, then POST /api/analyze-image with a real photo.
