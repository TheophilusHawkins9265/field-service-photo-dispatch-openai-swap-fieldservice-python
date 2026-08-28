import json
from types import SimpleNamespace

from field_dispatch_gateway.work_order_triage import (
    DispatchStatus,
    TriageRequest,
    WorkOrderPhoto,
    triage_work_order,
)


class FakeCompletions:
    def __init__(self) -> None:
        self.request: dict[str, object] = {}

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.request = kwargs
        decision = {
            "observed_condition": "Water is pooling beneath the compressor housing.",
            "recommended_action": "Keep the unit isolated and send the assigned technician.",
            "technician_follow_up": True,
        }
        message = SimpleNamespace(content=json.dumps(decision))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_dispatched_leak_photo_produces_technician_follow_up() -> None:
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    request = TriageRequest(
        work_order_id="WO-1842",
        dispatch_status=DispatchStatus.DISPATCHED,
        issue="Cooling unit is leaking after restart",
        photos=[
            WorkOrderPhoto(
                url="https://example.com/work-orders/WO-1842/compressor.jpg",
                caption="Compressor housing and the floor directly below it",
            )
        ],
    )

    result = triage_work_order(request, client)

    assert result.work_order_id == "WO-1842"
    assert result.technician_follow_up is True
    assert "assigned technician" in result.recommended_action
    assert completions.request["model"] == "auto"
    messages = completions.request["messages"]
    assert isinstance(messages, list)
    assert "dispatched" in str(messages[0])
    assert "compressor.jpg" in str(messages[0])
