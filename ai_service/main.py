import logging
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math

LOGGER = logging.getLogger("dentalink.ai")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="DentalLink AI Service")

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


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def appt_score(booking_lead_days: float, fee: float) -> float:
    # simple “risk” simulation: shorter lead + higher fee => higher probability
    x = (-0.25 * booking_lead_days) + (0.01 * fee)
    return sigmoid(x)


def payment_score(amount: float, days_overdue: float) -> float:
    # overdue dominates
    x = (0.35 * days_overdue) + (0.001 * amount)
    return sigmoid(x)


def treatment_score(cost: float) -> float:
    x = 0.01 * cost
    return sigmoid(x)


def risk_level(p: float, hi: float, med: float) -> str:
    return "High" if p >= hi else "Medium" if p >= med else "Low"


@app.post("/predict/appointment")
async def predict_appointment(body: AppointmentPayload) -> Dict[str, object]:
    try:
        p = appt_score(body.booking_lead_days, body.fee)
        response = {
            "predicted_no_show": bool(p >= 0.5),
            "risk_score": round(p, 4),
            "risk_level": risk_level(p, 0.67, 0.33),
        }
        LOGGER.info("appointment request=%s response=%s", body.model_dump(), response)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict/payment")
async def predict_payment(body: PaymentPayload) -> Dict[str, object]:
    try:
        p = payment_score(body.amount, body.days_overdue)
        response = {
            "predicted_late": bool(p >= 0.5),
            "risk_score": round(p, 4),
            "risk_level": risk_level(p, 0.7, 0.4),
        }
        LOGGER.info("payment request=%s response=%s", body.model_dump(), response)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict/treatment")
async def predict_treatment(body: TreatmentPayload) -> Dict[str, object]:
    try:
        p = treatment_score(body.cost)
        urgency_band = "Immediate" if p >= 0.75 else "Soon" if p >= 0.5 else "Routine"
        response = {
            "urgency_score": round(p * 100, 0),
            "note_category": "Emergency" if urgency_band == "Immediate" else "FollowUp" if urgency_band == "Soon" else "Routine",
            "recommended_next_step": f"Schedule {urgency_band.lower()} follow-up",
        }
        LOGGER.info("treatment request=%s response=%s", body.model_dump(), response)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/")
async def health() -> Dict[str, str]:
    return {"status": "ok"}
