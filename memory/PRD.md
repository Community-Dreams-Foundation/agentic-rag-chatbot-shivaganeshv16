# Agentic RAG Knowledge Assistant - PRD

## Original Problem Statement
Build a production-ready Agentic RAG Knowledge Assistant for a SaaS platform with document upload, citation-backed chat, persistent markdown memory, and weather analysis.

## Architecture
- **Frontend**: React + Tailwind CSS + shadcn/ui (port 3000)
- **Backend**: FastAPI + ChromaDB (in-memory) + Emergent LLM Key (port 8001)
- **Database**: MongoDB for document metadata, memory feed
- **LLM**: GPT-4.1-nano via Emergent integrations
- **Weather**: Open-Meteo API (free)

## User Personas
- Hackathon judges evaluating technical depth
- Developers uploading technical documentation
- Teams seeking AI-powered document Q&A

## Core Requirements
- [x] 3-pane dashboard (Knowledge, Chat, Memory)
- [x] Drag-and-drop file upload (PDF, MD, TXT)
- [x] Progress stepper (Parsing → Chunking → Indexing)
- [x] RAG chat with semantic retrieval via ChromaDB
- [x] Citations with clickable source chips
- [x] Thought trace accordion (reasoning steps)
- [x] Persistent memory (USER_MEMORY.md, COMPANY_MEMORY.md)
- [x] Autonomous memory extraction via LLM
- [x] Weather tool (Open-Meteo API with 24h rolling average + volatility)
- [x] Sanity check endpoint + artifacts/sanity_output.json
- [x] Makefile with `make sanity` command
- [x] Markdown + code highlighting in chat

## What's Been Implemented (Feb 2026)
- Full 3-pane dashboard with Manrope/Inter/JetBrains Mono fonts
- File upload with drag-drop, stepper UI, ChromaDB indexing
- RAG chat with hybrid retrieval, citations, thought trace
- Memory system with autonomous LLM-driven extraction
- Weather analysis with Open-Meteo (rolling avg, volatility)
- All API endpoints tested and working

## Prioritized Backlog
- P0: (none - MVP complete)
- P1: Streaming responses, chat history persistence
- P2: Multi-file upload, search within docs, export memory
- P3: Mobile responsive layout, dark mode toggle
