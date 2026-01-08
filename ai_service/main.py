import logging
from pathlib import Path
from typing import Any, Dict

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

LOGGER = logging.getLogger("dentalink.ai")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"


class AppointmentPayload(BaseModel):
    booking_lead_days: float = Field(..., description="Days between booking and appointment")
    fee: float = Field(..., description="Appointment fee amount")
    status: str = Field(..., description="Current appointment status")


class PaymentPayload(BaseModel):
    amount: float = Field(..., description="Payment amount")
    days_overdue: float = Field(..., description="Days past due date")
    method: str = Field(..., description="Payment method label")


class TreatmentPayload(BaseModel):
    cost: float = Field(..., description="Treatment cost")
    status: str = Field(..., description="Treatment status")
    type: str = Field(..., description="Treatment type")


class ModelRegistry:
    def __init__(self) -> None:
        self._models: Dict[str, Any] = {}

    def load_model(self, key: str, filename: str) -> None:
        model_path = MODELS_DIR / filename
        if not model_path.exists():
            raise FileNotFoundError(f"Model file missing: {model_path}")
        self._models[key] = joblib.load(model_path)
        LOGGER.info("Loaded model %s from %s", key, model_path)

    def predict(self, key: str, features: list[float]) -> Dict[str, Any]:
        model = self._models.get(key)
        if model is None:
            raise KeyError(f"Model not loaded: {key}")
        probability = float(model.predict_proba([features])[0][1]) if hasattr(model, "predict_proba") else float(model.predict([features])[0])
        label = bool(probability >= 0.5)
        return {"probability": probability, "label": label}


registry = ModelRegistry()


def load_models() -> None:
    registry.load_model("appointment", "appointment_model.joblib")
    registry.load_model("payment", "payment_model.joblib")
    registry.load_model("treatment", "treatment_model.joblib")


app = FastAPI(title="DentalLink AI Service")


@app.on_event("startup")
async def startup_event() -> None:
    load_models()


def log_io(endpoint: str, payload: Dict[str, Any], response: Dict[str, Any]) -> None:
    LOGGER.info("Endpoint %s request: %s", endpoint, payload)
    LOGGER.info("Endpoint %s response: %s", endpoint, response)


@app.post("/predict/appointment")
async def predict_appointment(body: AppointmentPayload) -> Dict[str, Any]:
    try:
        result = registry.predict("appointment", [body.booking_lead_days, body.fee])
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Appointment prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = {
        "predicted_no_show": result["label"],
        "risk_score": round(result["probability"], 4),
        "risk_level": "High" if result["probability"] >= 0.67 else "Medium" if result["probability"] >= 0.33 else "Low",
    }
    log_io("appointment", body.model_dump(), response)
    return response


@app.post("/predict/payment")
async def predict_payment(body: PaymentPayload) -> Dict[str, Any]:
    try:
        result = registry.predict("payment", [body.amount, body.days_overdue])
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Payment prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = {
        "predicted_late": result["label"],
        "risk_score": round(result["probability"], 4),
        "risk_level": "High" if result["probability"] >= 0.7 else "Medium" if result["probability"] >= 0.4 else "Low",
    }
    log_io("payment", body.model_dump(), response)
    return response


@app.post("/predict/treatment")
async def predict_treatment(body: TreatmentPayload) -> Dict[str, Any]:
    try:
        result = registry.predict("treatment", [body.cost])
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Treatment prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    urgency_band = "Immediate" if result["probability"] >= 0.75 else "Soon" if result["probability"] >= 0.5 else "Routine"
    response = {
        "urgency_score": round(result["probability"] * 100, 0),
        "note_category": "Emergency" if urgency_band == "Immediate" else "FollowUp" if urgency_band == "Soon" else "Routine",
        "recommended_next_step": f"Schedule {urgency_band.lower()} follow-up",
    }
    log_io("treatment", body.model_dump(), response)
    return response


@app.get("/")
async def health() -> Dict[str, str]:
    return {"status": "ok"}
