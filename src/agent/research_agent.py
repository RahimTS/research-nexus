import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
import asyncio

from src.models.schemas import (
    ResearchReport, ResearchStatus
)
from src.agent.tools import research_tools
from src.database.db import db
from src.utils.config import settings
from src.utils.llm_factory import create_llm

class ResearchState(TypedDict):
    messages: List[Any]
    query: str
    research_id: str
    current_step: int
    max_steps: int
    search_results: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    report: Dict[str, Any]
    final_report: Optional[ResearchReport]
    error: str

class ResearchAgent:
    def __init__(self):
        self.llm = create_llm()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the research workflow graph"""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("plan_research", self._plan_research)
        workflow.add_node("search_information", self._search_information)
        workflow.add_node("analyze_results", self._analyze_results)
        workflow.add_node("synthesize_report", self._synthesize_report)
        workflow.add_node("finalize_report", self._finalize_report)
        
        # Add edges
        workflow.set_entry_point("plan_research")
        workflow.add_edge("plan_research", "search_information")
        workflow.add_edge("search_information", "analyze_results")
        workflow.add_edge("analyze_results", "synthesize_report")
        workflow.add_edge("synthesize_report", "finalize_report")
        workflow.add_edge("finalize_report", END)
        
        return workflow.compile()
    
    async def _plan_research(self, state: ResearchState) -> ResearchState:
        """Plan the research approach"""
        print(f"Planning research for: {state['query']}")
        
        # Update database status
        db.update_status(state['research_id'], ResearchStatus.SEARCHING)
        
        # Generate search queries using LLM
        system_message = SystemMessage(content="""
        You are a research planning assistant. Given a research query, break it down into 2-3 specific search queries 
        that will help gather comprehensive information. Return only the search queries, one per line.
        """)
        
        human_message = HumanMessage(content=f"Research query: {state['query']}")
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            search_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
            
            state['search_queries'] = search_queries[:3]  # Limit to 3 queries
            state['messages'] = add_messages(state['messages'], [human_message, response])
            
        except Exception as e:
            state['error'] = f"Planning error: {str(e)}"
            state['search_queries'] = [state['query']]  # Fallback to original query
        
        return state
    
    async def _search_information(self, state: ResearchState) -> ResearchState:
        """Search for information using planned queries"""
        print("Searching for information...")
        
        all_results = []
        search_queries = state.get('search_queries', [state['query']])
        
        for query in search_queries:
            try:
                results = research_tools.search_web(query, max_results=settings.max_search_results)
                all_results.extend(results)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Search error for query '{query}': {e}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        state['search_results'] = unique_results
        print(f"Found {len(unique_results)} unique sources")
        
        return state
    
    async def _analyze_results(self, state: ResearchState) -> ResearchState:
        """Analyze the search results"""
        print("Analyzing search results...")
        
        # Update database status
        db.update_status(state['research_id'], ResearchStatus.ANALYZING)
        
        if not state['search_results']:
            state['analysis'] = {
                'summary': 'No search results found.',
                'key_findings': [],
                'confidence': 0.0
            }
            return state
        
        try:
            # Use LLM to analyze results (if available)
            if self.llm is None:
                print("No LLM available, using fallback analysis")
                state['analysis'] = self._basic_analysis_fallback(state['search_results'], state['query'])
                return state
                
            system_message = SystemMessage(content="""
            You are a research analyst. Analyze the provided search results and extract:
            1. Key findings (3-5 main points)
            2. Important insights
            3. Any conflicting information
            4. Confidence level (0-1) based on source quality and consistency
            
            Format your response as:
            KEY FINDINGS:
            - Point 1
            - Point 2
            ...
            
            INSIGHTS:
            Your analysis here
            
            CONFIDENCE: 0.X
            """)
            
            # Prepare content for analysis
            content_summary = "\n\n".join([
                f"Source: {result['title']}\nURL: {result['url']}\nContent: {result['content'][:500]}..."
                for result in state['search_results'][:5]  # Limit to top 5 results
            ])
            
            human_message = HumanMessage(content=f"Research Query: {state['query']}\n\nSearch Results:\n{content_summary}")
            
            response = await self.llm.ainvoke([system_message, human_message])
            
            # Parse response (simplified)
            response_text = response.content
            key_findings = []
            insights = ""
            confidence = 0.5
            
            if "KEY FINDINGS:" in response_text:
                findings_section = response_text.split("KEY FINDINGS:")[1].split("INSIGHTS:")[0]
                key_findings = [line.strip("- ").strip() for line in findings_section.split('\n') if line.strip().startswith('-')]
            
            if "INSIGHTS:" in response_text:
                insights = response_text.split("INSIGHTS:")[1].split("CONFIDENCE:")[0].strip()
            
            if "CONFIDENCE:" in response_text:
                try:
                    confidence = float(response_text.split("CONFIDENCE:")[1].strip())
                except:
                    confidence = 0.5
            
            state['analysis'] = {
                'key_findings': key_findings,
                'insights': insights,
                'confidence': confidence,
                'total_sources': len(state['search_results'])
            }
            
        except Exception as e:
            print(f"Analysis error (falling back to basic analysis): {e}")
            # Fallback to basic analysis without LLM
            state['analysis'] = self._basic_analysis_fallback(state['search_results'], state['query'])
        
        return state
    
    def _basic_analysis_fallback(self, search_results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Fallback analysis when LLM is unavailable"""
        if not search_results:
            return {
                'key_findings': [],
                'insights': 'No search results available for analysis.',
                'confidence': 0.0,
                'total_sources': 0
            }
        
        # Extract key findings from titles and content
        key_findings = []
        all_content = ""
        
        for result in search_results[:5]:
            # Add title as potential finding
            if result.get('title'):
                key_findings.append(f"Found information about: {result['title']}")
            
            # Collect content for basic insight generation
            all_content += result.get('content', '')[:200] + " "
        
        # Basic insight generation
        insights = f"Analysis of {len(search_results)} sources related to '{query}'. "
        insights += f"Sources cover various aspects including: {', '.join([r['title'][:50] for r in search_results[:3]])}."
        
        # Basic confidence calculation
        avg_relevance = sum(result.get('relevance_score', 0.5) for result in search_results) / len(search_results)
        confidence = min(avg_relevance * 0.8, 0.85)  # Cap at 0.85 for basic analysis
        
        return {
            'key_findings': key_findings[:5],
            'insights': insights,
            'confidence': round(confidence, 2),
            'total_sources': len(search_results)
        }
    
    async def _synthesize_report(self, state: ResearchState) -> ResearchState:
        """Synthesize the final research report"""
        print("Synthesizing research report...")
        
        # Update database status
        try:
            db.update_status(state['research_id'], ResearchStatus.SYNTHESIZING)
        except Exception as e:
            print(f"Database status update error: {e}")
        
        try:
            if self.llm is None:
                print("No LLM available, using fallback synthesis")
                analysis = state.get('analysis', {})
                state['report'] = {
                    'executive_summary': f"Research completed on '{state['query']}' with {analysis.get('total_sources', 0)} sources.",
                    'detailed_analysis': analysis.get('insights', 'Analysis completed with available data.'),
                    'key_findings': analysis.get('key_findings', []),
                    'confidence_score': analysis.get('confidence', 0.5)
                }
                return state
            
            system_message = SystemMessage(content="""
            You are a research report writer. Create a comprehensive research report with:
            1. Executive Summary (2-3 sentences)
            2. Detailed Analysis (2-3 paragraphs)
            3. Conclusion
            
            Be objective, cite the quality of sources, and provide actionable insights.
            """)
            
            analysis = state.get('analysis', {})
            human_message = HumanMessage(content=f"""
            Research Query: {state['query']}
            
            Key Findings:
            {chr(10).join(f"- {finding}" for finding in analysis.get('key_findings', []))}
            
            Insights: {analysis.get('insights', '')}
            
            Sources: {analysis.get('total_sources', 0)} sources analyzed
            Confidence: {analysis.get('confidence', 0.5)}
            
            Please create a comprehensive research report.
            """)
            
            response = await self.llm.ainvoke([system_message, human_message])
            
            # Parse the report (simplified - in production, you'd use more sophisticated parsing)
            report_text = response.content
            
            # Try to extract executive summary (first paragraph)
            paragraphs = [p.strip() for p in report_text.split('\n\n') if p.strip()]
            executive_summary = paragraphs[0] if paragraphs else "Research completed successfully."
            
            state['report'] = {
                'executive_summary': executive_summary,
                'detailed_analysis': report_text,
                'key_findings': analysis.get('key_findings', []),
                'confidence_score': analysis.get('confidence', 0.5)
            }
            
        except Exception as e:
            print(f"Synthesis error (falling back): {e}")
            # Fallback report
            analysis = state.get('analysis', {})
            state['report'] = {
                'executive_summary': f"Research completed on '{state['query']}' with {analysis.get('total_sources', 0)} sources.",
                'detailed_analysis': analysis.get('insights', 'Analysis completed with available data.'),
                'key_findings': analysis.get('key_findings', []),
                'confidence_score': analysis.get('confidence', 0.5)
            }
        
        return state
    
    async def _finalize_report(self, state: ResearchState) -> ResearchState:
        """Finalize and save the research report"""
        print("Finalizing research report...")
        
        try:
            report_data = state['report']
            
            # Create sources list
            sources = [
                {
                    'title': result['title'],
                    'url': result['url'],
                    'relevance_score': str(result.get('relevance_score', 0.5))
                }
                for result in state['search_results']
            ]
            
            # Create the final report
            final_report = ResearchReport(
                id=state['research_id'],
                query=state['query'],
                status=ResearchStatus.COMPLETED,
                executive_summary=report_data.get('executive_summary', 'Research completed successfully.'),
                key_findings=report_data.get('key_findings', []),
                detailed_analysis=report_data.get('detailed_analysis', 'Analysis completed.'),
                sources=sources,
                confidence_score=report_data.get('confidence_score', 0.5),
                total_sources=len(sources),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                processing_time_seconds=None  # Will be set by the main method
            )
            
            # Save to database
            success = db.save_report(final_report)
            if not success:
                print("Failed to save report to database")
            
            state['final_report'] = final_report
            
        except Exception as e:
            print(f"Finalization error: {e}")
            state['error'] = str(e)
            
            # Try to update status to failed
            try:
                db.update_status(state['research_id'], ResearchStatus.FAILED)
            except Exception as db_error:
                print(f"Database error: {db_error}")
        
        return state
    
    async def research(self, query: str, research_id: str = None) -> ResearchReport:
        """Main research method"""
        if not research_id:
            research_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        # Initialize state
        initial_state = ResearchState(
            messages=[],
            query=query,
            research_id=research_id,
            current_step=0,
            max_steps=settings.max_research_steps,
            search_results=[],
            analysis={},
            report={},
            final_report=None,
            error=""
        )
        
        # Create initial report in database
        initial_report = ResearchReport(
            id=research_id,
            query=query,
            status=ResearchStatus.STARTED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        try:
            db.save_report(initial_report)
        except Exception as e:
            print(f"Error saving initial report: {e}")
        
        try:
            # Run the research workflow
            final_state = await self.graph.ainvoke(initial_state)
            
            if final_state.get('error'):
                # Handle error case
                error_report = ResearchReport(
                    id=research_id,
                    query=query,
                    status=ResearchStatus.FAILED,
                    executive_summary=f"Research failed: {final_state['error']}",
                    processing_time_seconds=time.time() - start_time,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                try:
                    db.save_report(error_report)
                except Exception as e:
                    print(f"Error saving error report: {e}")
                return error_report
            
            # Update processing time
            final_report = final_state.get('final_report')
            if final_report:
                final_report.processing_time_seconds = time.time() - start_time
                final_report.updated_at = datetime.now()
                try:
                    db.save_report(final_report)
                except Exception as e:
                    print(f"Error updating final report: {e}")
                return final_report
            else:
                # Create a basic success report if final_report is missing
                return ResearchReport(
                    id=research_id,
                    query=query,
                    status=ResearchStatus.COMPLETED,
                    executive_summary="Research completed successfully.",
                    processing_time_seconds=time.time() - start_time,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            
        except Exception as e:
            print(f"Research workflow error: {e}")
            error_report = ResearchReport(
                id=research_id,
                query=query,
                status=ResearchStatus.FAILED,
                executive_summary=f"Research failed due to system error: {str(e)}",
                processing_time_seconds=time.time() - start_time,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            try:
                db.save_report(error_report)
            except Exception as db_e:
                print(f"Error saving error report: {db_e}")
            return error_report

# Global agent instance
research_agent = ResearchAgent()