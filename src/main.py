import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import List

from src.models.schemas import (
    ResearchQuery, ResearchResponse, ResearchReport, 
    ResearchListResponse, ResearchStatus
)
from src.agent.research_agent import research_agent
from src.database.db import db
from src.utils.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 AI Research Agent starting up...")
    print(f"📊 Database: {settings.database_url}")
    print(f"🤖 LLM Model: {settings.llm_model}")
    print(f"🔍 Search: {'Tavily API' if settings.tavily_api_key else 'Mock Search'}")
    print(f"🌐 API: {'OpenRouter' if settings.openrouter_api_key else 'None (Fallback mode)'}")
    yield
    # Shutdown
    print("🔄 AI Research Agent shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AI Research Agent",
    description="An intelligent research assistant that can search, analyze, and synthesize information from multiple sources",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AI Research Agent API",
        "version": "1.0.0",
        "status": "healthy",
        "features": {
            "search_engine": "Tavily API" if settings.tavily_api_key else "Mock Search",
            "llm_model": settings.llm_model,
            "llm_provider": "OpenRouter" if settings.openrouter_api_key else "Fallback",
            "max_sources": settings.max_search_results
        }
    }

@app.post("/research", response_model=ResearchResponse)
async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
    """Start a new research task"""
    if not query.query.strip():
        raise HTTPException(status_code=400, detail="Research query cannot be empty")
    
    # Generate research ID
    import uuid
    research_id = str(uuid.uuid4())
    
    # Start research in background
    background_tasks.add_task(run_research_task, query.query, research_id)
    
    return ResearchResponse(
        research_id=research_id,
        status=ResearchStatus.STARTED,
        message=f"Research started for query: '{query.query}'"
    )

@app.post("/research/sync", response_model=ResearchResponse)
async def research_sync(query: ResearchQuery):
    """Run research synchronously (blocking)"""
    if not query.query.strip():
        raise HTTPException(status_code=400, detail="Research query cannot be empty")
    
    try:
        report = await research_agent.research(query.query)
        return ResearchResponse(
            research_id=report.id,
            status=report.status,
            message="Research completed successfully" if report.status == ResearchStatus.COMPLETED else "Research failed",
            report=report
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.get("/research/{research_id}", response_model=ResearchResponse)
async def get_research(research_id: str):
    """Get research results by ID"""
    report = db.get_report(research_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Research not found")
    
    message = {
        ResearchStatus.STARTED: "Research is starting...",
        ResearchStatus.SEARCHING: "Searching for information...",
        ResearchStatus.ANALYZING: "Analyzing search results...",
        ResearchStatus.SYNTHESIZING: "Synthesizing research report...",
        ResearchStatus.COMPLETED: "Research completed successfully",
        ResearchStatus.FAILED: "Research failed"
    }.get(report.status, "Unknown status")
    
    return ResearchResponse(
        research_id=research_id,
        status=report.status,
        message=message,
        report=report
    )

@app.get("/research", response_model=ResearchListResponse)
async def list_research(page: int = 1, per_page: int = 20):
    """List all research reports with pagination"""
    if per_page > 100:
        per_page = 100
    
    offset = (page - 1) * per_page
    reports = db.list_reports(limit=per_page, offset=offset)
    
    # Get total count (simplified - in production, you'd have a separate count query)
    total = len(db.list_reports(limit=1000))  # Rough count
    
    return ResearchListResponse(
        research_reports=reports,
        total=total,
        page=page,
        per_page=per_page
    )

@app.delete("/research/{research_id}")
async def delete_research(research_id: str):
    """Delete a research report"""
    report = db.get_report(research_id)
    if not report:
        raise HTTPException(status_code=404, detail="Research not found")
    
    # In a full implementation, you'd add a delete method to the database
    return {"message": "Delete functionality not implemented yet"}

async def run_research_task(query: str, research_id: str):
    """Background task to run research"""
    try:
        await research_agent.research(query, research_id)
    except Exception as e:
        print(f"Background research task failed: {e}")
        # Update status to failed
        db.update_status(research_id, ResearchStatus.FAILED)

# Development server configuration
if __name__ == "__main__":
    import os
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=int(settings.port),
        reload=settings.debug_mode,
        log_level=settings.log_level.lower(),
        timeout_keep_alive=5,
        reload_dirs=[os.getcwd()],
    )