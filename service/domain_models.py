from typing import List, Literal

from pydantic import BaseModel, Field, HttpUrl


DispatchStatus = Literal["dispatched", "onsite_complete", "follow_up_needed", "closed"]
FollowUpStatus = Literal["close_ready", "return_visit_required", "awaiting_dispatch_review"]


class IngestWorkOrderRequest(BaseModel):
    collection: str = Field(min_length=1)
    work_order_id: str = Field(min_length=1)
    customer_name: str = Field(min_length=1)
    dispatch_status: DispatchStatus
    technician_name: str = Field(min_length=1)
    pdf_url: HttpUrl


class IngestWorkOrderResponse(BaseModel):
    work_order_id: str
    chunks_indexed: int
    dispatch_status: DispatchStatus


class AnswerDispatchQuestionRequest(BaseModel):
    collection: str = Field(min_length=1)
    work_order_id: str = Field(min_length=1)
    question: str = Field(min_length=3)


class EvidenceSnippet(BaseModel):
    text: str
    score: float


class AnswerDispatchQuestionResponse(BaseModel):
    work_order_id: str
    question: str
    answer: str
    follow_up_status: FollowUpStatus
    recommended_action: str
    evidence: List[EvidenceSnippet]
