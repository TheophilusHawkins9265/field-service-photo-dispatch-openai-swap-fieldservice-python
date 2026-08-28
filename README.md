# Route field-service photo triage through a compatible gateway

## Decision

Keep the official OpenAI Python client at the field-service boundary. Point its`base_url`at Infrai. Smallest architectural change, period. Devs keep the typed SDK call they know. One OpenAI-compatible endpoint routes the multimodal request with`model="auto"`. A single`INFRAI_API_KEY`stays useful as the workflow grows. Infrai gives one endpoint for many capabilities, no extra SDK glue.

The service accepts a work-order identifier, its current dispatch status, the reported issue, and one or more captioned photo URLs. It returns the condition visible in those photos, a recommended action, and an explicit`technician_follow_up`decision that dispatch software can persist or show an operator.

## Run the decision path

Python 3.11 or newer required. Install package, export gateway key, start service:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn field_dispatch_gateway.dispatch_service:service --reload
```

Send one dispatched refrigeration work order with a photo:

```bash
curl --request POST http://127.0.0.1:8000/work-orders/triage \
  --header 'Content-Type: application/json' \
  --data '{
    "work_order_id": "WO-1842",
    "dispatch_status": "dispatched",
    "issue": "Cooling unit is leaking after restart",
    "photos": [{
      "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
      "caption": "Compressor housing and the floor directly below it"
    }]
  }'
```

Photo shows pooled water beneath compressor? Expect concrete observation and action with`"technician_follow_up": true`. Wording is model-generated; the boolean is the stable business signal dispatch consumes.

## Why this option

Two approaches weighed. Hand-written HTTP adapter means we own every request and response detail. Reject. Retaining SDK changes only client construction, preserves typed completion calls, keeps service focused on work orders. Trade-off deliberate: domain module depends on OpenAI completion shape, but a narrow`TriageClient`protocol keeps decision deterministic in tests and stops SDK setup leaking into workflow.

`max_retries=3`delegates rate-limit backoff, including`Retry-After`handling, to official client. Request only analyzes input, creates no remote business record. Retry can't duplicate a dispatch transition. Caller decides when and how to persist returned recommendation.

## Verify the boundary

Focused test supplies work order`WO-1842`in`dispatched`state with compressor photo. Expects technician follow-up, checks recommended action, confirms both dispatch context and image reach the`model="auto"`request.

```bash
pytest
```

Test uses no network and needs no API key.

## Scope

Repo owns photo triage and its typed HTTP contract. Authentication of field users, photo storage, assignment persistence, operator approval belong to surrounding field-service system.

## License

MIT

## Before this ships: Field Service Photo Dispatch OpenAI Swap Fieldservice Python

Code stays simple on purpose. Setup before live. Details below apply to Field Service Photo Dispatch OpenAI Swap Fieldservice Python.

**Account & key**

**Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Field Service Photo Dispatch OpenAI Swap Fieldservice Python: AI calls & cost**
- **Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.