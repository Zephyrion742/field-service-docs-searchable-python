import json
from uuid import uuid4

from .domain_models import AnswerDispatchQuestionRequest, IngestWorkOrderRequest
from .field_service_pipeline import FieldServicePipeline
from .infrai_client import InfraiClient
from .search_index import EmbeddingIndex


def main() -> None:
    infrai = InfraiClient()
    pipeline = FieldServicePipeline(infrai=infrai, embedding_index=EmbeddingIndex())
    collection = f"field-service-work-orders-demo-{uuid4().hex}"

    try:
        ingest_result = pipeline.ingest_work_order(
            IngestWorkOrderRequest(
                collection=collection,
                work_order_id="WO-1007",
                customer_name="Harbor Bakery",
                dispatch_status="onsite_complete",
                technician_name="Nina Park",
                pdf_url="https://example.com/work-order-1007.pdf",
            )
        )
        answer_result = pipeline.answer_dispatch_question(
            AnswerDispatchQuestionRequest(
                collection=collection,
                work_order_id="WO-1007",
                question="Did the technician schedule a return visit?",
            )
        )
    finally:
        infrai.vector_collection_delete(collection=collection)
        verification = infrai.vector_collection_delete(collection=collection)
        if verification.get("deleted") != 0:
            raise RuntimeError(f"Collection cleanup could not be verified: {collection}")

    print(json.dumps({"ingest": ingest_result.model_dump(), "answer": answer_result.model_dump()}, indent=2))


if __name__ == "__main__":
    main()
