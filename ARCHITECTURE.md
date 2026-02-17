# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Port 3000)                │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Knowledge    │  │   Agentic    │  │   Memory Feed     │  │
│  │  Manager      │  │   Chat       │  │   (Live sidebar)  │  │
│  │  (File Upload)│  │   (RAG Q&A)  │  │                   │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
└─────────┼─────────────────┼────────────────────┼────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8001)                  │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ /api/upload  │  │ /api/chat    │  │ /api/memory-feed    │ │
│  │ /api/docs    │  │ /api/sanity  │  │ /api/memory/{type}  │ │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬───────────┘ │
│         │                │                     │              │
│         ▼                ▼                     ▼              │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────────┐   │
│  │  ChromaDB   │  │  Gemini LLM  │  │  Memory Files      │   │
│  │  (In-Memory)│  │  (2.5 Flash) │  │  (USER/COMPANY.md) │   │
│  └────────────┘  └──────┬───────┘  └────────────────────┘   │
│                         │                                     │
│                  ┌──────┴───────┐                             │
│                  │  Open-Meteo  │                             │
│                  │  Weather API │                             │
│                  └──────────────┘                             │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                    MongoDB                            │    │
│  │  Collections: documents, memory_feed                  │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

## Ingestion Pipeline

1. **File Upload**: User uploads PDF, MD, or TXT via drag-and-drop
2. **Parsing**: PyPDF2 extracts text from PDFs; UTF-8 decode for MD/TXT
3. **Chunking**: 500-word sliding window with 50-word overlap to preserve context
4. **Indexing**: Chunks are embedded and stored in ChromaDB with metadata (source filename, chunk index, document ID)
5. **Storage**: Document metadata stored in MongoDB for listing/management

## Retrieval & Citations

- **Semantic Search**: User query is embedded and compared against ChromaDB using cosine similarity
- **Relevance Filtering**: Only chunks with distance < 1.5 are included (prevents irrelevant matches)
- **Context Building**: Retrieved chunks are formatted with source attribution: `[Source: filename, Chunk N]`
- **Grounded Response**: LLM receives only retrieved context + system rules. If no relevant docs found, it explicitly states so
- **Citations**: Each response includes source chips linking back to the document and chunk number

## Memory Logic

The memory subsystem runs after each chat response:

1. **Decision Call**: A separate Gemini call analyzes the conversation
2. **JSON Structure**: Returns `{should_write: bool, target: "user"|"company", fact: string}`
3. **Filtering**: Only facts with `should_write: true` are persisted
4. **Storage**: Facts appended to `USER_MEMORY.md` or `COMPANY_MEMORY.md` with timestamps
5. **Feed**: Memory entries also stored in MongoDB for the real-time sidebar feed

**User Memory**: Preferences, roles, recurring tasks, personal context
**Company Memory**: Organizational patterns, bugs, workflow insights, team learnings

## Weather Tool (Open-Meteo)

- **Detection**: Keyword matching for weather-related terms in user queries
- **API Call**: Async HTTP request to Open-Meteo's free forecast API
- **Analysis**: Computes 24h rolling average temperature, min/max range, volatility (standard deviation), humidity, wind speed
- **Safety**: API calls are isolated; no environment variables exposed to the weather tool
- **Cities**: 12+ pre-configured cities with lat/lon coordinates

## Security Considerations

- Environment variables loaded via dotenv, never hardcoded
- Weather API calls isolated from app environment
- MongoDB `_id` fields excluded from all API responses
- File upload restricted to PDF, MD, TXT only
- CORS configured via environment variable
