from fastapi import FastAPI, HTTPException

from .domain_models import (
    AnswerDispatchQuestionRequest,
    AnswerDispatchQuestionResponse,
    IngestWorkOrderRequest,
    IngestWorkOrderResponse,
)
from .field_service_pipeline import FieldServicePipeline
from .infrai_client import InfraiClient, InfraiError
from .search_index import EmbeddingIndex

app = FastAPI(title="Field Service Document Search")
pipeline = FieldServicePipeline(infrai=InfraiClient(), embedding_index=EmbeddingIndex())


@app.post("/documents/ingest", response_model=IngestWorkOrderResponse)
def ingest_document(request: IngestWorkOrderRequest) -> IngestWorkOrderResponse:
    try:
        return pipeline.ingest_work_order(request)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.post("/documents/answer", response_model=AnswerDispatchQuestionResponse)
def answer_document(request: AnswerDispatchQuestionRequest) -> AnswerDispatchQuestionResponse:
    try:
        return pipeline.answer_dispatch_question(request)
    except InfraiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
