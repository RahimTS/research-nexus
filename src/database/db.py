import json
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path
from src.models.schemas import ResearchReport, ResearchStatus

class ResearchDatabase:
    def __init__(self, db_url: str = None):
        # Parse SQLite URL or use default
        if db_url and db_url.startswith("sqlite:///"):
            self.db_path = db_url.replace("sqlite:///", "")
        elif db_url and db_url.startswith("sqlite://"):
            self.db_path = db_url.replace("sqlite://", "")
        else:
            self.db_path = db_url or "research_agent.db"
        
        # Remove ./ prefix if present
        if self.db_path.startswith("./"):
            self.db_path = self.db_path[2:]
            
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_reports (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    status TEXT NOT NULL,
                    executive_summary TEXT DEFAULT '',
                    key_findings TEXT DEFAULT '[]',
                    detailed_analysis TEXT DEFAULT '',
                    sources TEXT DEFAULT '[]',
                    research_steps TEXT DEFAULT '[]',
                    confidence_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    total_sources INTEGER DEFAULT 0,
                    processing_time_seconds REAL
                )
            """)
            conn.commit()
    
    def save_report(self, report: ResearchReport) -> bool:
        """Save or update a research report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO research_reports 
                    (id, query, status, executive_summary, key_findings, detailed_analysis, 
                     sources, research_steps, confidence_score, created_at, updated_at, 
                     total_sources, processing_time_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.id,
                    report.query,
                    report.status,
                    report.executive_summary,
                    json.dumps(report.key_findings),
                    report.detailed_analysis,
                    json.dumps(report.sources),
                    json.dumps([step.dict() for step in report.research_steps]),
                    report.confidence_score,
                    report.created_at.isoformat(),
                    report.updated_at.isoformat(),
                    report.total_sources,
                    report.processing_time_seconds
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def get_report(self, report_id: str) -> Optional[ResearchReport]:
        """Get a research report by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM research_reports WHERE id = ?", (report_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return ResearchReport(
                        id=row['id'],
                        query=row['query'],
                        status=ResearchStatus(row['status']),
                        executive_summary=row['executive_summary'],
                        key_findings=json.loads(row['key_findings']),
                        detailed_analysis=row['detailed_analysis'],
                        sources=json.loads(row['sources']),
                        research_steps=[],  # We'll load these separately if needed
                        confidence_score=row['confidence_score'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        total_sources=row['total_sources'],
                        processing_time_seconds=row['processing_time_seconds']
                    )
        except Exception as e:
            print(f"Error getting report: {e}")
        return None
    
    def list_reports(self, limit: int = 50, offset: int = 0) -> List[ResearchReport]:
        """List all research reports with pagination"""
        reports = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM research_reports 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                
                for row in cursor.fetchall():
                    reports.append(ResearchReport(
                        id=row['id'],
                        query=row['query'],
                        status=ResearchStatus(row['status']),
                        executive_summary=row['executive_summary'],
                        key_findings=json.loads(row['key_findings']),
                        detailed_analysis=row['detailed_analysis'],
                        sources=json.loads(row['sources']),
                        research_steps=[],
                        confidence_score=row['confidence_score'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at']),
                        total_sources=row['total_sources'],
                        processing_time_seconds=row['processing_time_seconds']
                    ))
        except Exception as e:
            print(f"Error listing reports: {e}")
        return reports
    
    def update_status(self, report_id: str, status: ResearchStatus) -> bool:
        """Update the status of a research report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE research_reports 
                    SET status = ?, updated_at = ? 
                    WHERE id = ?
                """, (status.value, datetime.now().isoformat(), report_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False

# Global database instance
from src.utils.config import settings
db = ResearchDatabase(settings.database_url)