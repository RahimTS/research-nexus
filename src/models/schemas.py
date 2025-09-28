from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class ResearchStatus(str, Enum):
    STARTED = "started"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"

class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    relevance_score: float = Field(ge=0, le=1)

class ResearchStep(BaseModel):
    step_number: int
    description: str
    query: str
    results: List[SearchResult]
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ResearchQuery(BaseModel):
    query: str = Field(min_length=10, max_length=500, description="Research question or topic")
    depth: str = Field(default="standard", description="Research depth: quick, standard, or deep")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific areas to focus on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the latest developments in AI agents?",
                "depth": "standard",
                "focus_areas": ["LangGraph", "AI agents", "autonomous systems"]
            }
        }

class ResearchReport(BaseModel):
    id: str
    query: str
    status: ResearchStatus
    executive_summary: str = ""
    key_findings: List[str] = []
    detailed_analysis: str = ""
    sources: List[Dict[str, str]] = []
    research_steps: List[ResearchStep] = []
    confidence_score: float = Field(ge=0, le=1, default=0.0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_sources: int = 0
    processing_time_seconds: Optional[float] = None
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "id": "abc-123-def",
                "query": "What are the latest AI developments?",
                "status": "completed",
                "executive_summary": "Recent AI developments show significant progress...",
                "key_findings": ["Finding 1", "Finding 2"],
                "confidence_score": 0.85
            }
        }

class ResearchResponse(BaseModel):
    research_id: str
    status: ResearchStatus
    message: str
    report: Optional[ResearchReport] = None

class ResearchListResponse(BaseModel):
    research_reports: List[ResearchReport]
    total: int
    page: int
    per_page: int