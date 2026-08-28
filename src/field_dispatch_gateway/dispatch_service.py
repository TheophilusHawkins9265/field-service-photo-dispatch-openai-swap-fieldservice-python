"""HTTP entry point for the field-service triage workflow."""

from fastapi import FastAPI, HTTPException
from openai import APIError

from .work_order_triage import TriageDecision, TriageRequest, gateway_client, triage_work_order

service = FastAPI(title="Field-service photo dispatch")


@service.post("/work-orders/triage", response_model=TriageDecision)
def create_triage(request: TriageRequest) -> TriageDecision:
    try:
        return triage_work_order(request, gateway_client())
    except (APIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Triage response could not be completed") from exc
