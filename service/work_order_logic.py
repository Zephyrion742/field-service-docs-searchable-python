from typing import Dict, List

from .domain_models import AnswerDispatchQuestionResponse, EvidenceSnippet


def split_ocr_text(text: str, work_order_id: str, technician_name: str) -> List[Dict[str, object]]:
    cleaned = " ".join(text.split())
    parts = [part.strip() for part in cleaned.split(".") if part.strip()]
    chunks: List[Dict[str, object]] = []
    for index, part in enumerate(parts):
        chunks.append(
            {
                "id": f"{work_order_id}-chunk-{index}",
                "text": part,
                "metadata": {
                    "work_order_id": work_order_id,
                    "technician_name": technician_name,
                    "chunk_index": index,
                },
            }
        )
    return chunks


def decide_follow_up(question: str, matches: List[Dict[str, object]], work_order_id: str) -> AnswerDispatchQuestionResponse:
    evidence: List[EvidenceSnippet] = []
    combined = []
    for match in matches:
        metadata = match.get("metadata") or {}
        text = str(metadata.get("text", "")).strip()
        score = float(match.get("score", 0.0))
        if text:
            combined.append(text.lower())
            evidence.append(EvidenceSnippet(text=text, score=score))

    corpus = " ".join(combined)
    needs_return = any(phrase in corpus for phrase in ["return ", "come back", "ordered", "backorder", "temporary"])
    close_ready = any(phrase in corpus for phrase in ["tested okay", "job complete", "no return needed", "resolved"]) and not needs_return

    if needs_return:
        return AnswerDispatchQuestionResponse(
            work_order_id=work_order_id,
            question=question,
            answer="Yes. The technician documented a temporary fix and a scheduled return visit after ordering a part.",
            follow_up_status="return_visit_required",
            recommended_action="Keep the dispatch open and confirm the return appointment with the customer.",
            evidence=evidence,
        )

    if close_ready:
        return AnswerDispatchQuestionResponse(
            work_order_id=work_order_id,
            question=question,
            answer="The notes read like a completed visit with no further technician action required.",
            follow_up_status="close_ready",
            recommended_action="Close the dispatch and send the completion summary.",
            evidence=evidence,
        )

    return AnswerDispatchQuestionResponse(
        work_order_id=work_order_id,
        question=question,
        answer="The notes do not clearly confirm closure or a scheduled return visit.",
        follow_up_status="awaiting_dispatch_review",
        recommended_action="Have dispatch review the work order before changing status.",
        evidence=evidence,
    )
