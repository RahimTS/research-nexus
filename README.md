# 🔬 AI Research Agent

An intelligent research assistant that can search, analyze, and synthesize information from multiple sources using LangGraph and modern AI tools.

## 🌟 Features

- **🤖 Agentic AI**: Multi-step reasoning with LangGraph workflow
- **🔍 Smart Search**: Powered by Tavily API for high-quality web results
- **📊 Synthesis**: Automatically synthesizes findings from multiple sources
- **⚡ FastAPI Backend**: RESTful API with async support
- **💾 Persistent Storage**: SQLite database for research history
- **🎯 Confidence Scoring**: AI-powered confidence assessment
- **📱 Interactive API**: Auto-generated docs with FastAPI

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   LangGraph     │    │   Tavily API    │
│   REST API      │───▶│   Research      │───▶│   Web Search    │
│                 │    │   Agent         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         ▼              ┌─────────────────┐              │
┌─────────────────┐    │   OpenRouter     │              │
│   SQLite DB     │    │   Analysis &     │              │
│   Research      │◀───│   Synthesis      │              │
│   History       │    │                 │              │
└─────────────────┘    └─────────────────┘              │
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenRouter API Key ([Get one here](https://openrouter.ai/keys))
- Tavily API Key ([Get one here](https://tavily.com/)) - 1000 free searches

### Installation

1. **Clone and setup**:
```bash
git clone https://github.com/RahimTS/research-nexus.git
cd research-nexus
uv sync
```

2. **Environment setup**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Run the application**:
```bash
uv run python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Test it out**:
- Open http://localhost:8000/docs
- Try the `/research/sync` endpoint with a query

## 📚 API Endpoints

### `POST /research/sync`
Run research synchronously (blocking)
```json
{
  "query": "What are the latest developments in quantum computing?",
  "depth": "standard"
}
```

### `POST /research`
Start research in background (non-blocking)

### `GET /research/{research_id}`
Get research results by ID

### `GET /research`
List all research reports with pagination

## 🧠 How It Works

1. **Planning**: Breaks down your query into focused search terms
2. **Searching**: Uses Tavily API to find relevant, high-quality sources
3. **Analysis**: LLM analyzes and extracts key insights from sources
4. **Synthesis**: Creates a comprehensive research report with citations
5. **Storage**: Saves everything to database with confidence scores

## 📊 Example Output

```json
{
  "research_id": "abc-123",
  "status": "completed",
  "report": {
    "executive_summary": "Recent developments in quantum computing include...",
    "key_findings": [
      "IBM announced a 1000-qubit quantum processor",
      "Google achieved quantum advantage in error correction"
    ],
    "detailed_analysis": "The field of quantum computing has seen remarkable progress...",
    "sources": [
      {"title": "IBM's Quantum Breakthrough", "url": "...", "relevance_score": "0.95"}
    ],
    "confidence_score": 0.87,
    "total_sources": 8
  }
}
```

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **LangGraph**: Agentic AI workflow orchestration
- **LangChain**: LLM integration and tools
- **OpenRouter**: Access to multiple LLM models (GPT, Claude, etc.)
- **Tavily API**: Specialized search for AI agents
- **SQLite**: Lightweight database
- **Pydantic**: Data validation and serialization
- **UV**: Fast Python package management

## 🎯 Use Cases

- **Research Reports**: Academic or business research
- **Market Analysis**: Industry trends and competitor analysis  
- **Due Diligence**: Investment or partnership research
- **Content Creation**: Background research for articles/blogs
- **Learning**: Explore complex topics with AI guidance

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | Required |
| `TAVILY_API_KEY` | Tavily API key for web search | Required |
| `LLM_MODEL` | LLM model to use | `gpt-3.5-turbo` |
| `TEMPERATURE` | LLM temperature (0.0-1.0) | `0.1` |
| `MAX_SEARCH_RESULTS` | Maximum search results per query | `5` |
| `MAX_RESEARCH_STEPS` | Maximum research workflow steps | `3` |

### Supported LLM Models

The application supports any model available through OpenRouter:

- `gpt-3.5-turbo` (default)
- `anthropic/claude-3-haiku`
- `meta-llama/llama-3.1-8b-instruct`
- `google/gemini-pro`
- And many more...

## 🏗️ Project Structure

```
research-nexus/
├── src/
│   ├── agent/
│   │   ├── research_agent.py    # Main research workflow
│   │   └── tools.py             # Search and analysis tools
│   ├── database/
│   │   └── db.py                # Database operations
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   ├── utils/
│   │   ├── config.py             # Configuration management
│   │   └── llm_factory.py        # LLM initialization
│   └── main.py                   # FastAPI application
├── tests/                        # Test files
├── .env.example                  # Environment template
├── pyproject.toml                # Project dependencies
└── README.md                     # This file
```

## 🚧 Future Enhancements

- [ ] Multi-language support
- [ ] PDF/document upload and analysis
- [ ] Research templates for different domains
- [ ] Collaborative research sessions
- [ ] Export to various formats (PDF, Word, etc.)
- [ ] Integration with knowledge management tools

## 📝 Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black src/
uv run ruff check src/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - feel free to use for personal or commercial projects!

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) for AI framework
- [LangGraph](https://github.com/langchain-ai/langgraph) for workflow orchestration
- [OpenRouter](https://openrouter.ai/) for LLM access
- [Tavily](https://tavily.com/) for web search capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework

---

**Built with ❤️ using modern AI tools and frameworks**