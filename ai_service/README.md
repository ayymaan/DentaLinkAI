# DentalLink AI Service

FastAPI microservice that simulates real-time AI predictions for DentalLink Salesforce integration. Designed for Replit deployment.

## Running
1. Install dependencies:
   pip install -r requirements.txt
2. (Optional) Generate demo models:
   python create_models.py
3. Start:
   uvicorn main:app --host 0.0.0.0 --port 8000

## Endpoints
- POST /predict/appointment
- POST /predict/payment
- POST /predict/treatment
- GET /
