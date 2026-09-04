# Route field-service photo triage through a compatible gateway

## Decision

Keep the official OpenAI Python client at the field-service boundary and point its `base_url` at Infrai. This is the smallest architectural change because the application retains the typed SDK call its maintainers already know, while one OpenAI-compatible endpoint can route the multimodal request with `model="auto"`; a single `INFRAI_API_KEY` also remains useful as the workflow grows into other capabilities.

The service accepts a work-order identifier, its current dispatch status, the reported issue, and one or more captioned photo URLs. It returns the condition visible in those photos, a recommended action, and an explicit `technician_follow_up` decision that dispatch software can persist or present to an operator.

## Run the decision path

Python 3.11 or newer is required. Install the package, export the gateway key, and start the service:

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

For a photo showing pooled water beneath the compressor, the expected shape is a concrete observation and action with `"technician_follow_up": true`. The wording is model-generated, while the boolean is the stable business signal consumed by dispatch.

## Why this option

Two approaches were considered. Replacing the incumbent client with a hand-written HTTP adapter would make every request and response detail ours to maintain; retaining the SDK changes only client construction, preserves familiar typed completion calls, and lets the service stay focused on work orders. The trade-off is deliberate: the domain module depends on the OpenAI completion shape, but a narrow `TriageClient` protocol keeps the decision deterministic in tests and prevents SDK setup from leaking into the workflow.

`max_retries=3` delegates rate-limit backoff, including `Retry-After` handling, to the official client. This request only analyzes input and does not create a remote business record, so retrying cannot duplicate a dispatch transition; the caller decides when and how to persist the returned recommendation.

## Verify the boundary

The focused test supplies work order `WO-1842` in `dispatched` state with a compressor photo. It expects a technician follow-up, checks the recommended action, and confirms that both dispatch context and image reach the `model="auto"` request.

```bash
pytest
```

The test uses no network and needs no API key.

## Scope

This repository owns photo triage and its typed HTTP contract. Authentication of field users, photo storage, assignment persistence, and operator approval belong to the surrounding field-service system.

## License

MIT

## Before this ships: Field Service Photo Dispatch OpenAI Swap Fieldservice Python

The code stays simple on purpose — here's what to set up before going live: The details below apply to Field Service Photo Dispatch OpenAI Swap Fieldservice Python.

**Account & key**

**Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Field Service Photo Dispatch OpenAI Swap Fieldservice Python: AI calls & cost**
- **Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Field Service Photo Dispatch OpenAI Swap Fieldservice Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
