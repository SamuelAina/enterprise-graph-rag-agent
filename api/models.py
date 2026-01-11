from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=4000)
    user_id: Optional[str] = Field(default="anonymous", max_length=128)
    session_id: Optional[str] = Field(default=None, max_length=128)
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SourceDoc(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AskResponse(BaseModel):
    answer: str
    trace_id: str
    route: str
    sources: List[SourceDoc] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
