import { useState, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { toast } from "sonner";
import KnowledgePanel from "@/components/KnowledgePanel";
import ChatPanel from "@/components/ChatPanel";
import MemoryFeed from "@/components/MemoryFeed";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Brain, Layers, Sparkles, RotateCcw, Loader2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function App() {
  const [documents, setDocuments] = useState([]);
  const [memoryEntries, setMemoryEntries] = useState([]);
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  const [resetting, setResetting] = useState(false);
  const chatResetRef = useRef(null);

  const handleDocumentUploaded = useCallback((doc) => {
    setDocuments((prev) => [...prev, doc]);
  }, []);

  const handleDocumentDeleted = useCallback((docId) => {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  }, []);

  const handleMemoryUpdate = useCallback((entries) => {
    if (entries && entries.length > 0) {
      setMemoryEntries((prev) => [...entries, ...prev]);
    }
  }, []);

  const handleResetAll = async () => {
    if (resetting) return;
    setResetting(true);
    try {
      await axios.delete(`${API}/reset`);
      setDocuments([]);
      setMemoryEntries([]);
      setSessionId(crypto.randomUUID());
      if (chatResetRef.current) chatResetRef.current();
      toast.success("All data cleared. Fresh start!");
    } catch (e) {
      toast.error("Failed to reset. Try again.");
    } finally {
      setResetting(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="h-screen flex flex-col bg-[#F8F9FA] overflow-hidden">
        {/* Header */}
        <header
          data-testid="app-header"
          className="flex-shrink-0 bg-white/80 backdrop-blur-md border-b border-slate-200 px-6 py-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-600 text-white">
                <Brain className="w-5 h-5" strokeWidth={1.5} />
              </div>
              <div>
                <h1 className="font-heading text-lg font-bold text-slate-900 tracking-tight leading-tight">
                  RAG Knowledge Assistant
                </h1>
                <p className="text-xs text-slate-500 font-medium">
                  Agentic retrieval with citations & memory
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    data-testid="reset-all-btn"
                    onClick={handleResetAll}
                    disabled={resetting}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-red-50 border border-red-200 text-red-600 hover:bg-red-100 hover:border-red-300 transition-colors duration-200 disabled:opacity-50"
                  >
                    {resetting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
                    ) : (
                      <RotateCcw className="w-3.5 h-3.5" strokeWidth={1.5} />
                    )}
                    <span className="text-xs font-medium">Reset</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent>Clear all docs, memory & chat</TooltipContent>
              </Tooltip>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-medium text-emerald-700">
                  Agent Online
                </span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200">
                <Layers className="w-3.5 h-3.5 text-slate-500" strokeWidth={1.5} />
                <span className="text-xs font-medium text-slate-600">
                  {documents.length} docs
                </span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-200">
                <Sparkles className="w-3.5 h-3.5 text-indigo-500" strokeWidth={1.5} />
                <span className="text-xs font-medium text-indigo-700">
                  {memoryEntries.length} memories
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Main 3-Pane Layout */}
        <main className="flex-1 flex overflow-hidden">
          {/* Left: Knowledge Manager (20%) */}
          <aside
            data-testid="knowledge-panel"
            className="w-[280px] flex-shrink-0 border-r border-slate-200 bg-white overflow-y-auto"
          >
            <KnowledgePanel
              documents={documents}
              setDocuments={setDocuments}
              onDocumentUploaded={handleDocumentUploaded}
              onDocumentDeleted={handleDocumentDeleted}
            />
          </aside>

          {/* Center: Chat (flex-1) */}
          <section
            data-testid="chat-panel"
            className="flex-1 flex flex-col min-w-0 bg-[#F8F9FA]"
          >
            <ChatPanel
              sessionId={sessionId}
              onMemoryUpdate={handleMemoryUpdate}
            />
          </section>

          {/* Right: Memory Feed (25%) */}
          <aside
            data-testid="memory-panel"
            className="w-[280px] flex-shrink-0 border-l border-slate-200 bg-white overflow-y-auto"
          >
            <MemoryFeed memoryEntries={memoryEntries} />
          </aside>
        </main>

        <Toaster position="bottom-right" />
      </div>
    </TooltipProvider>
  );
}

export default App;
