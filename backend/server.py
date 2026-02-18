from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import json
import uuid
import httpx
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import chromadb
from google import genai

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

DOCUMENTS_STORE: List[Dict[str, Any]] = []
MEMORY_FEED: List[Dict[str, Any]] = []

# ChromaDB in-memory
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(
    name="documents",
    metadata={"hnsw:space": "cosine"}
)

# Memory files
USER_MEMORY_PATH = ROOT_DIR / "USER_MEMORY.md"
COMPANY_MEMORY_PATH = ROOT_DIR / "COMPANY_MEMORY.md"
for p in [USER_MEMORY_PATH, COMPANY_MEMORY_PATH]:
    if not p.exists():
        p.write_text(f"# {'User' if 'USER' in p.name else 'Company'} Memory\n\n")

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
FRONT_END_URL = os.environ.get('FRONT_END_URL','')
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# --- CORS setup ---
cors_raw = os.environ.get("CORS_ORIGINS", FRONT_END_URL)
cors_origins = [origin.strip() for origin in cors_raw.split(",") if origin.strip()]
if not cors_origins:
    cors_origins = ["*"]
allow_credentials = "*" not in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- Models ---
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class Citation(BaseModel):
    source: str
    page: Optional[int] = None
    chunk: str

class ThoughtStep(BaseModel):
    step: str
    detail: str

class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target: str
    fact: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatResponse(BaseModel):
    response: str
    citations: List[Citation] = []
    thoughts: List[ThoughtStep] = []
    memory_updates: List[MemoryEntry] = []


# --- Utilities ---
def parse_file(content: bytes, filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext in ('md', 'txt'):
        return content.decode('utf-8', errors='ignore')
    return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    if not chunks and text.strip():
        chunks.append(text.strip())
    return chunks


async def fetch_weather_data(query: str) -> Optional[Dict]:
    cities = {
        "london": (51.5074, -0.1278, "London"),
        "paris": (48.8566, 2.3522, "Paris"),
        "tokyo": (35.6762, 139.6503, "Tokyo"),
        "new york": (40.7128, -74.0060, "New York"),
        "san francisco": (37.7749, -122.4194, "San Francisco"),
        "berlin": (52.5200, 13.4050, "Berlin"),
        "sydney": (-33.8688, 151.2093, "Sydney"),
        "mumbai": (19.0760, 72.8777, "Mumbai"),
        "dubai": (25.2048, 55.2708, "Dubai"),
        "singapore": (1.3521, 103.8198, "Singapore"),
        "los angeles": (34.0522, -118.2437, "Los Angeles"),
        "chicago": (41.8781, -87.6298, "Chicago"),
    }
    lat, lon, location_name = 40.7128, -74.0060, "New York"
    for city, (c_lat, c_lon, c_name) in cities.items():
        if city in query.lower():
            lat, lon, location_name = c_lat, c_lon, c_name
            break
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
                    "forecast_days": 3, "timezone": "auto"
                },
                timeout=10
            )
            data = resp.json()

        temps = data.get("hourly", {}).get("temperature_2m", [])[:24]
        humidity = data.get("hourly", {}).get("relative_humidity_2m", [])[:24]
        wind = data.get("hourly", {}).get("wind_speed_10m", [])[:24]

        avg_temp = sum(temps) / len(temps) if temps else 0
        max_temp = max(temps) if temps else 0
        min_temp = min(temps) if temps else 0
        avg_humidity = sum(humidity) / len(humidity) if humidity else 0
        avg_wind = sum(wind) / len(wind) if wind else 0

        volatility = 0
        if len(temps) > 1:
            mean = avg_temp
            variance = sum((t - mean) ** 2 for t in temps) / len(temps)
            volatility = variance ** 0.5

        return {
            "location": location_name,
            "summary": f"{location_name}: Avg {avg_temp:.1f} C, Range {min_temp:.1f}-{max_temp:.1f} C",
            "avg_temperature_24h": round(avg_temp, 1),
            "max_temperature": round(max_temp, 1),
            "min_temperature": round(min_temp, 1),
            "temperature_volatility": round(volatility, 2),
            "avg_humidity": round(avg_humidity, 1),
            "avg_wind_speed": round(avg_wind, 1),
            "hourly_temps": temps,
            "unit": "celsius"
        }
    except Exception as e:
        logger.error(f"Weather fetch error: {e}")
        return None


async def write_memory(entry: MemoryEntry):
    path = USER_MEMORY_PATH if entry.target == "user" else COMPANY_MEMORY_PATH
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with open(path, 'a') as f:
        f.write(f"\n- [{timestamp}] {entry.fact}\n")
    MEMORY_FEED.append({
        "id": entry.id,
        "target": entry.target,
        "fact": entry.fact,
        "timestamp": entry.timestamp
    })


async def decide_memory(user_message: str, ai_response: str) -> List[MemoryEntry]:
    """Use Gemini to decide if high-signal facts should be saved to memory"""
    entries = []
    try:
        prompt = (
            "Analyze this conversation and extract high-signal facts worth remembering.\n"
            "Return ONLY a valid JSON array. Each item: "
            '{\"should_write\": true, \"target\": \"user\" or \"company\", \"fact\": \"string\"}\n'
            "- user target: user preferences, roles, recurring tasks, personal context\n"
            "- company target: org patterns, discovered bugs, workflow insights, team learnings\n"
            "- Only extract genuinely useful, reusable facts. Be selective.\n"
            "- If nothing noteworthy, return: []\n"
            "- Return ONLY the JSON array, no markdown, no explanation.\n\n"
            f"User: {user_message}\nAssistant: {ai_response}"
        )
        result = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        result_text = result.text.strip()
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        decisions = json.loads(result_text)
        for d in decisions:
            if d.get('should_write'):
                entries.append(MemoryEntry(target=d.get('target', 'user'), fact=d.get('fact', '')))
    except Exception as e:
        logger.warning(f"Memory decision error: {e}")
    return entries


def build_system_prompt(context: str, weather_data: Optional[Dict], has_context: bool) -> str:
    prompt = (
        "You are an Agentic RAG Knowledge Assistant for a SaaS platform.\n\n"
        "RULES:\n"
        "1. If document context is provided, answer based on that context and cite sources with [Source: filename, Chunk N].\n"
        "2. If no relevant documents found for a docs query, say: \"I couldn't find that in your files.\"\n"
        "3. If weather data is provided, analyze it thoroughly - compute rolling averages, volatility, and explain findings.\n"
        "4. Use markdown formatting. Use code blocks for technical content.\n"
        "5. Be concise but thorough.\n"
    )
    if has_context:
        prompt += f"\n## Retrieved Document Context:\n{context}\n"
    if weather_data:
        prompt += f"\n## Weather Data (from Open-Meteo):\n{json.dumps(weather_data, indent=2)}\n"
    return prompt


# --- Routes ---
@api_router.get("/")
async def root():
    return {"message": "Agentic RAG Knowledge Assistant API"}

@api_router.get("/health")
async def health_check():
    """A simple status endpoint to verify the backend is running."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "storage": "in-memory",
        "documents_indexed": collection.count()
    }


@api_router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    allowed = {'pdf', 'md', 'txt'}
    ext = file.filename.lower().rsplit('.', 1)[-1]
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(allowed)}")

    content = await file.read()
    text = parse_file(content, file.filename)
    if not text.strip():
        raise HTTPException(400, "Could not extract text from file")

    chunks = chunk_text(text)
    doc_id = str(uuid.uuid4())

    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file.filename, "chunk_index": i, "doc_id": doc_id} for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids, metadatas=metadatas)

    doc_info = {
        "id": doc_id,
        "filename": file.filename,
        "file_type": ext,
        "chunks": len(chunks),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    DOCUMENTS_STORE.append(doc_info)

    return {"id": doc_id, "filename": file.filename, "chunks": len(chunks), "status": "indexed"}


@api_router.get("/documents")
async def list_documents():
    return DOCUMENTS_STORE.copy()


@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    try:
        results = collection.get(where={"doc_id": doc_id})
        if results['ids']:
            collection.delete(ids=results['ids'])
    except Exception:
        pass
    global DOCUMENTS_STORE
    DOCUMENTS_STORE[:] = [doc for doc in DOCUMENTS_STORE if doc["id"] != doc_id]
    return {"status": "deleted"}


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    thoughts = []
    citations = []

    # Step 1: Weather detection
    weather_data = None
    weather_kws = ['weather', 'temperature', 'forecast', 'climate', 'rain', 'wind', 'humidity', 'hot', 'cold']
    is_weather = any(kw in request.message.lower() for kw in weather_kws)

    if is_weather:
        thoughts.append(ThoughtStep(step="Weather Detection", detail="Weather query detected. Calling Open-Meteo API..."))
        weather_data = await fetch_weather_data(request.message)
        if weather_data:
            thoughts.append(ThoughtStep(step="Weather Data Retrieved", detail=f"Got data for {weather_data['location']}: {weather_data['summary']}"))

    # Step 2: Hybrid retrieval
    thoughts.append(ThoughtStep(step="Searching Documents", detail="Performing semantic search in ChromaDB..."))
    context_chunks = []
    try:
        count = collection.count()
        if count > 0:
            results = collection.query(query_texts=[request.message], n_results=min(5, count))
            if results and results['documents'] and results['documents'][0]:
                for doc, meta, dist in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    context_chunks.append({
                        'text': doc,
                        'source': meta.get('source', 'unknown'),
                        'chunk_index': meta.get('chunk_index', 0),
                        'distance': dist
                    })
                    citations.append(Citation(
                        source=meta.get('source', 'unknown'),
                        page=meta.get('chunk_index', 0) + 1,
                        chunk=doc[:150] + ('...' if len(doc) > 150 else '')
                    ))
    except Exception as e:
        logger.warning(f"ChromaDB search error: {e}")

    has_context = bool(context_chunks)
    if has_context:
        thoughts.append(ThoughtStep(step="Documents Found", detail=f"Found {len(context_chunks)} relevant chunks from uploaded documents"))
    else:
        thoughts.append(ThoughtStep(step="No Documents", detail="No relevant documents found in knowledge base"))

    context_text = "\n\n".join([f"[Source: {c['source']}, Chunk {c['chunk_index']+1}]\n{c['text']}" for c in context_chunks])

    # Step 3: LLM call
    thoughts.append(ThoughtStep(step="Generating Response", detail="Calling Gemini AI with retrieved context..."))
    system_msg = build_system_prompt(context_text, weather_data, has_context)

    try:
        full_prompt = f"{system_msg}\n\nUser question: {request.message}"
        response_text = None
        for attempt in range(3):
            try:
                gemini_response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt
                )
                response_text = gemini_response.text
                break
            except Exception as retry_err:
                if "429" in str(retry_err) and attempt < 2:
                    logger.info(f"Rate limited, retrying in {(attempt+1)*20}s...")
                    await asyncio.sleep((attempt + 1) * 20)
                else:
                    raise retry_err
        if response_text is None:
            response_text = "I encountered an error generating a response. Please try again."
    except Exception as e:
        logger.error(f"LLM error: {e}")
        response_text = "I encountered an error generating a response. Please try again."

    if not has_context and not is_weather:
        citations = []

    # Step 4: Memory decision
    memory_updates = []
    thoughts.append(ThoughtStep(step="Updating Memory", detail="Analyzing conversation for high-signal facts..."))
    try:
        memory_updates = await decide_memory(request.message, response_text)
        if memory_updates:
            for entry in memory_updates:
                await write_memory(entry)
            thoughts.append(ThoughtStep(step="Memory Written", detail=f"Extracted {len(memory_updates)} fact(s) to memory"))
        else:
            thoughts.append(ThoughtStep(step="No Memory Update", detail="No high-signal facts detected in this exchange"))
    except Exception as e:
        logger.warning(f"Memory error: {e}")
        thoughts.append(ThoughtStep(step="Memory Skipped", detail="Memory analysis skipped due to rate limits"))

    return ChatResponse(
        response=response_text,
        citations=citations[:5],
        thoughts=thoughts,
        memory_updates=memory_updates
    )


@api_router.get("/memory/{memory_type}")
async def get_memory(memory_type: str):
    if memory_type not in ("user", "company"):
        raise HTTPException(400, "memory_type must be 'user' or 'company'")
    path = USER_MEMORY_PATH if memory_type == "user" else COMPANY_MEMORY_PATH
    content = path.read_text() if path.exists() else ""
    return {"type": memory_type, "content": content}


@api_router.get("/memory-feed")
async def get_memory_feed():
    return sorted(MEMORY_FEED, key=lambda entry: entry["timestamp"], reverse=True)[:50]


@api_router.delete("/reset")
async def reset_all():
    """Clear all documents, memory files, and memory feed"""
    global collection
    # Clear ChromaDB
    try:
        chroma_client.delete_collection("documents")
        collection = chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    except Exception as e:
        logger.warning(f"ChromaDB reset error: {e}")

    DOCUMENTS_STORE.clear()
    MEMORY_FEED.clear()

    # Reset memory files
    USER_MEMORY_PATH.write_text("# User Memory\n\n")
    COMPANY_MEMORY_PATH.write_text("# Company Memory\n\n")

    return {"status": "reset", "message": "All data cleared successfully"}


@api_router.get("/sanity")
async def sanity_check():
    artifacts_dir = ROOT_DIR / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    test_query = "What is this system about?"
    try:
        result = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=test_query
        )
        response = result.text
    except Exception:
        response = "Sanity check - LLM unavailable"

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_query": test_query,
        "agent_response": response,
        "citations": [],
        "documents_indexed": len(DOCUMENTS_STORE),
        "status": "ok"
    }
    with open(artifacts_dir / "sanity_output.json", "w") as f:
        json.dump(output, f, indent=2)
    return output


app.include_router(api_router)
