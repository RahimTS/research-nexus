import asyncio
import httpx
from typing import List, Dict, Any
from langchain.tools import tool
from tavily import TavilyClient
from bs4 import BeautifulSoup
from src.utils.config import settings

class ResearchTools:
    def __init__(self):
        self.tavily_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web for information on a given query"""
        try:
            if self.tavily_client:
                print(f"🔍 Searching with Tavily: {query}")
                # Use Tavily for better search results
                response = self.tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results,
                    include_domains=None,
                    exclude_domains=None
                )
                
                results = []
                for result in response.get('results', []):
                    results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', '')[:1500],  # Limit content length
                        'relevance_score': result.get('score', 0.8)  # Tavily usually gives good scores
                    })
                print(f"✅ Found {len(results)} results")
                return results
            else:
                print(f"⚠️ No Tavily API key, using fallback search")
                return self._fallback_search(query, max_results)
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return self._fallback_search(query, max_results)
    
    def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Fallback search method when Tavily is not available"""
        # This is a mock implementation - in production, you'd use DuckDuckGo API or similar
        return [
            {
                'title': f"Mock result for: {query}",
                'url': "https://example.com",
                'content': f"This is mock content related to {query}. In a real implementation, this would contain actual search results.",
                'relevance_score': 0.7
            }
        ]
    
    @tool
    def extract_key_points(self, content: str, topic: str) -> List[str]:
        """Extract key points from content related to a specific topic"""
        # This would typically use an LLM to extract key points
        # For now, we'll use a simple approach
        sentences = content.split('.')
        key_points = []
        
        topic_words = topic.lower().split()
        for sentence in sentences[:10]:  # Limit to first 10 sentences
            sentence = sentence.strip()
            if len(sentence) > 20 and any(word in sentence.lower() for word in topic_words):
                key_points.append(sentence)
        
        return key_points[:5]  # Return top 5 key points
    
    @tool
    def synthesize_information(self, search_results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Synthesize information from multiple search results"""
        if not search_results:
            return {
                'summary': 'No search results found.',
                'key_findings': [],
                'confidence': 0.0
            }
        
        # Combine all content
        all_content = ' '.join([result.get('content', '') for result in search_results])
        
        # Extract key findings (simplified version)
        key_findings = []
        for result in search_results:
            if result.get('content'):
                points = self.extract_key_points(result['content'], query)
                key_findings.extend(points)
        
        # Calculate confidence based on number of sources and relevance scores
        avg_relevance = sum(result.get('relevance_score', 0.5) for result in search_results) / len(search_results)
        source_count_factor = min(len(search_results) / 5.0, 1.0)  # Max confidence at 5+ sources
        confidence = (avg_relevance * 0.7) + (source_count_factor * 0.3)
        
        return {
            'summary': f"Found {len(search_results)} sources related to: {query}",
            'key_findings': list(set(key_findings))[:10],  # Remove duplicates, limit to 10
            'confidence': round(confidence, 2),
            'source_count': len(search_results)
        }
    
    async def fetch_url_content(self, url: str) -> str:
        """Fetch content from a URL"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:2000]  # Limit content length
        except Exception as e:
            print(f"Error fetching URL content: {e}")
            return ""

# Global tools instance
research_tools = ResearchTools()