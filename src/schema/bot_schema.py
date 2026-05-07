from pydantic import BaseModel
from typing import List, Optional
from fastapi import UploadFile

class ChatRequest(BaseModel):
    question: str
    selected_resume_ids: Optional[List[str]] = None
    session_id: Optional[str] = None

class CandidateResult(BaseModel):
    resume_id: str
    candidate_name: str
    summary: str
    score: float
    decision: str  # "Shortlist" / "Reject"

class ChatResponse(BaseModel):
    answer: str
    candidates: List[CandidateResult]
    used_resume_ids: List[str]

class UploadResponse(BaseModel):
    resume_id: str
    candidate_name: str
    message: str