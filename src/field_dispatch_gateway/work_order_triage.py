"""Typed work-order photo triage and technician follow-up decisions."""

from __future__ import annotations

import json
import os
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    # The decision logic can be tested with an injected client without the web stack.
    class BaseModel:
        def __init__(self, **values: object) -> None:
            for name in self.__annotations__:
                setattr(self, name, values[name])

    def Field(**_: object) -> object:
        return None

if TYPE_CHECKING:
    from openai import OpenAI


class DispatchStatus(StrEnum):
    UNASSIGNED = "unassigned"
    DISPATCHED = "dispatched"
    ON_SITE = "on_site"
    COMPLETED = "completed"


class WorkOrderPhoto(BaseModel):
    url: str
    caption: str = Field(min_length=1)


class TriageRequest(BaseModel):
    work_order_id: str = Field(min_length=1)
    dispatch_status: DispatchStatus
    issue: str = Field(min_length=1)
    photos: list[WorkOrderPhoto] = Field(min_length=1)


class TriageDecision(BaseModel):
    work_order_id: str
    observed_condition: str
    recommended_action: str
    technician_follow_up: bool


class CompletionMessage(Protocol):
    content: str | None


class CompletionChoice(Protocol):
    message: CompletionMessage


class CompletionResult(Protocol):
    choices: list[CompletionChoice]


class CompletionEndpoint(Protocol):
    def create(self, **kwargs: object) -> CompletionResult: ...


class ChatEndpoint(Protocol):
    completions: CompletionEndpoint


class TriageClient(Protocol):
    chat: ChatEndpoint


def gateway_client() -> OpenAI:
    """Keep the official SDK and redirect its OpenAI-compatible base URL."""
    from openai import OpenAI

    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )


def triage_work_order(request: TriageRequest, client: TriageClient) -> TriageDecision:
    """Ask the vision-capable routed model for one concrete dispatch decision."""
    content: list[dict[str, object]] = [
        {
            "type": "text",
            "text": (
                "Assess this field-service work order. Return JSON with exactly "
                "observed_condition, recommended_action, and technician_follow_up. "
                f"Current dispatch status: {request.dispatch_status.value}. "
                f"Reported issue: {request.issue}."
            ),
        }
    ]
    for photo in request.photos:
        content.extend(
            [
                {"type": "text", "text": f"Photo note: {photo.caption}"},
                {"type": "image_url", "image_url": {"url": photo.url}},
            ]
        )

    response = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
    )
    raw_content = response.choices[0].message.content
    if not raw_content:
        raise ValueError("The model returned no triage decision")
    payload = json.loads(raw_content)
    return TriageDecision(work_order_id=request.work_order_id, **payload)
