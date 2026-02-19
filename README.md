# Agentic RAG Knowledge Assistant

## Participant Info (Required)
- **Full Name:** Shiva Ganesh Vankdoth
- **Email:** shivaganeshv16@gmail.com
- **GitHub Username:** shivaganeshv16

## Live Website URL
https://agentic-rag-bot.vercel.app/

## Video Walkthrough
https://drive.google.com/drive/u/0/folders/1YBfluwEd0CnWCjWRJQcttXO8ZH2jXQa4

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd agentic-rag-chatbot

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Set up environment variables
# Edit backend/.env with your keys:
#   GEMINI_API_KEY="your-gemini-api-key"
#   FRONT_END_URL=http://localhost:3000
#   CORS_ORIGINS=http://localhost:3000

# 4. Start backend
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# 5. Install frontend dependencies (in another terminal)
cd frontend
npm install

# 6. Set up frontend env
# Edit frontend/.env:
#   REACT_APP_BACKEND_URL=http://localhost:8001

# 7. Start frontend
npm start

# 8. Open http://localhost:3000 in your browser

# 9. Run sanity check
cd ..
make sanity 
If Terminal
Invoke-WebRequest -Uri http://localhost:8001/api/sanity | Select-Object -ExpandProperty Content | python -m json.tool
```


## Features Implemented

### Feature A - File Upload + RAG (Core)
- **Upload**: Drag-and-drop file upload supporting PDF, MD, and TXT files
- **Processing Pipeline**: Parse → Chunk (500-word sliding window with overlap) → Index in ChromaDB
- **Retrieval**: Semantic vector search via ChromaDB with cosine similarity
- **Citations**: Every AI response includes source citations with clickable chips showing `[filename: Page N]`
- **Groundedness**: If no relevant docs found, agent says "I couldn't find that in your files"
- **Progress Stepper**: Visual stepper showing Parsing → Chunking → Indexing progress

### Feature B - Persistent Memory (Core)
- **Autonomous Extraction**: Agent uses Gemini to decide what's worth remembering after each conversation
- **USER_MEMORY.md**: Stores user-specific preferences, roles, and recurring tasks
- **COMPANY_MEMORY.md**: Stores organizational learnings, discovered bugs, workflow insights
- **Decision Structure**: Uses `{should_write, target, fact}` JSON structure internally
- **Live Feed**: Real-time memory feed in the sidebar showing extracted facts
- **Selective**: Only high-signal, reusable facts are stored (no transcript dumping)

### Feature C - Safe Compute + Open-Meteo (Optional)
- **Weather Tool**: Agent detects weather queries and calls Open-Meteo API
- **Time Series Analysis**: Computes 24-hour rolling averages, temperature volatility (std dev), humidity, wind speed
- **12+ Cities**: Supports common cities (NYC, London, Tokyo, Paris, Berlin, etc.)
- **Safe Execution**: Weather API calls are isolated from environment variables
- **Clear Explanation**: Returns structured analysis with computed metrics

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture overview.

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, shadcn/ui, Lucide icons
- **Backend**: FastAPI, Python 3.11
- **Vector Store**: ChromaDB (in-memory)
- **LLM**: Google Gemini 2.5 Flash (free tier)
- **Storage**: Code Level Memory (document metadata, memory feed)
- **Weather API**: Open-Meteo (free, no key required)

## Evaluation
See [EVAL_QUESTIONS.md](EVAL_QUESTIONS.md) for suggested test prompts.
