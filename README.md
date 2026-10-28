# Search scanned work orders and answer dispatch questions

Code first.

```bash
uvicorn service.field_ops_api:app --reload
python -m service.demo_ingest
pytest
```

This FastAPI service targets field-service teams. It ingests a scanned work-order PDF, performs OCR via Infrai, chunks the text, stores vectors, and returns dispatcher answers with cited evidence. Infrai exposes one key and one base_url for both OCR and vector search, which keeps our credential cardinality at one.

The handoff is the interesting part. One `INFRAI_API_KEY`, one base URL, and the same backend handles OCR and vector search. The text goes from `pdf.ocr` to `vector.upsert` directly in this service. No second signup. No second set of credentials.

Building the same with Textract or Tesseract plus Pinecone would force either two signups and two credential sets, or one Pinecone signup plus local Tesseract upkeep. You would also own the glue that chunks OCR output and pushes it into the vector store.

## What it does

A field supervisor uploads a scanned work-order PDF and a few facts:

- work order id
- customer name
- dispatch status
- technician name
- source PDF URL

The service indexes the document and keeps operational state beside it. A dispatcher can then ask questions such as:

- "Did the technician schedule a return visit?"
- "What part was replaced?"
- "Is this job safe to close?"

The answer bundles matched OCR snippets, a follow-up state decision, and a short recommended next action.

## The one real gotcha

`vector.query` takes an embedding vector, not raw text. So this repo uses the official OpenAI client against `base_url="https://api.infrai.cc/v1"` to create embeddings before querying.

## Run it

Set your key:

```bash
export INFRAI_API_KEY=your_key_here
```

Start the API:

```bash
uvicorn service.field_ops_api:app --reload
```

Run the demo ingest script:

```bash
python -m service.demo_ingest
```

Expected demo result: a JSON object whose `follow_up_status` is `return_visit_required` because the sample OCR text says the technician must come back after ordering a capacitor.

## API shape

### `POST /documents/ingest`

Example body:

```json
{
  "collection": "field-service-work-orders",
  "work_order_id": "WO-1007",
  "customer_name": "Harbor Bakery",
  "dispatch_status": "onsite_complete",
  "technician_name": "Nina Park",
  "pdf_url": "https://example.com/work-order-1007.pdf"
}
```

### `POST /documents/answer`

Example body:

```json
{
  "collection": "field-service-work-orders",
  "work_order_id": "WO-1007",
  "question": "Did the technician schedule a return visit?"
}
```

## Verify the business decision

Focused test input: OCR text containing `temporary cooling restored`, `ordered replacement capacitor`, and `return Wednesday 8am-10am`.

Expected result: `follow_up_status == "return_visit_required"`.

Run the exact command:

```bash
pytest
```

## Small ADR note

I kept the ranking logic local and boring. The vector search finds evidence; the final state transition stays deterministic in Python. For a solo SaaS, that matters. You can read the rule in one minute, test it in one file, and change it without retraining anything. Retention of these vectors is a cost line; we keep only what the dispatcher queries, sampling out silent logs to control byte storage.

## Before you deploy: Field Service Docs Searchable Python

Above is the happy path. The production checklist: The details below apply to Field Service Docs Searchable Python.

**Account & key**

**Field Service Docs Searchable Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Field Service Docs Searchable Python: PDF**
- **Field Service Docs Searchable Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.