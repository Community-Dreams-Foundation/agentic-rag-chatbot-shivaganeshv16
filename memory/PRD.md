# Agentic RAG Knowledge Assistant - PRD

## Original Problem Statement
Build Agentic RAG chatbot for hackathon: File-grounded Q&A with citations, durable memory to markdown files, safe compute with Open-Meteo weather analysis.

## Architecture
- **Frontend**: React 19 + Tailwind CSS + shadcn/ui (port 3000)
- **Backend**: FastAPI + ChromaDB (in-memory) + Google Gemini 2.5 Flash (port 8001)
- **Database**: MongoDB (doc metadata, memory feed)
- **LLM**: Google Gemini 2.5 Flash (free tier, google-genai SDK)
- **Weather**: Open-Meteo API (free, no key)

## What's Been Implemented (Feb 2026)
- Feature A: RAG with upload (PDF/MD/TXT), parse, chunk, index, semantic retrieval, citations
- Feature B: Persistent memory - Gemini decides what to write to USER_MEMORY.md / COMPANY_MEMORY.md
- Feature C: Open-Meteo weather tool with 24h rolling average, volatility
- 3-pane dashboard UI with live memory feed
- Hackathon files: README.md, ARCHITECTURE.md, EVAL_QUESTIONS.md, Makefile, scripts/, sample_docs/
- Sanity check: `make sanity` → artifacts/sanity_output.json

## Prioritized Backlog
- P1: Streaming responses, BM25 hybrid retrieval, reranking
- P2: Conversation history persistence, multi-user support
- P3: Knowledge-graph RAG, section-aware chunking
