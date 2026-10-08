from typing import Dict, List

from .domain_models import (
    AnswerDispatchQuestionRequest,
    AnswerDispatchQuestionResponse,
    IngestWorkOrderRequest,
    IngestWorkOrderResponse,
)
from .infrai_client import InfraiClient
from .search_index import EmbeddingIndex
from .work_order_logic import decide_follow_up, split_ocr_text


class FieldServicePipeline:
    def __init__(self, infrai: InfraiClient, embedding_index: EmbeddingIndex):
        self.infrai = infrai
        self.embedding_index = embedding_index

    def ingest_work_order(self, request: IngestWorkOrderRequest) -> IngestWorkOrderResponse:
        ocr_data = self.infrai.pdf_ocr(pdf=str(request.pdf_url), lang="en", quality="high")
        ocr_text = self._extract_ocr_text(ocr_data)
        chunks = split_ocr_text(ocr_text, request.work_order_id, request.technician_name)
        embeddings = self.embedding_index.embed_texts([chunk["text"] for chunk in chunks])

        vectors: List[Dict[str, object]] = []
        for chunk, embedding in zip(chunks, embeddings):
            metadata = dict(chunk["metadata"])
            metadata.update(
                {
                    "text": chunk["text"],
                    "customer_name": request.customer_name,
                    "dispatch_status": request.dispatch_status,
                }
            )
            vectors.append(
                {
                    "id": chunk["id"],
                    "values": embedding,
                    "metadata": metadata,
                }
            )

        self.infrai.vector_upsert(collection=request.collection, vectors=vectors)
        return IngestWorkOrderResponse(
            work_order_id=request.work_order_id,
            chunks_indexed=len(vectors),
            dispatch_status=request.dispatch_status,
        )

    def answer_dispatch_question(self, request: AnswerDispatchQuestionRequest) -> AnswerDispatchQuestionResponse:
        embedding = self.embedding_index.embed_query(request.question)
        query_data = self.infrai.vector_query(
            collection=request.collection,
            embedding=embedding,
            top_k=5,
            filter={"work_order_id": request.work_order_id},
            include_metadata=True,
        )
        matches = self._extract_matches(query_data)
        return decide_follow_up(request.question, matches, request.work_order_id)

    @staticmethod
    def _extract_ocr_text(ocr_data: Dict[str, object]) -> str:
        if isinstance(ocr_data.get("text"), str):
            return str(ocr_data["text"])
        pages = ocr_data.get("pages")
        if isinstance(pages, list):
            texts = []
            for page in pages:
                if isinstance(page, dict) and isinstance(page.get("text"), str):
                    texts.append(page["text"])
            return "\n".join(texts)
        return ""

    @staticmethod
    def _extract_matches(query_data: Dict[str, object]) -> List[Dict[str, object]]:
        if isinstance(query_data.get("matches"), list):
            return [item for item in query_data["matches"] if isinstance(item, dict)]
        if isinstance(query_data.get("results"), list):
            return [item for item in query_data["results"] if isinstance(item, dict)]
        return []
