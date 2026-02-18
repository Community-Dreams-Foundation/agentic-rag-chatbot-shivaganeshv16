import { useState, useRef, useEffect } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  Send,
  Sparkles,
  User,
  FileSearch,
  CloudSun,
  Brain,
  Loader2,
  Copy,
  Check,
  ChevronRight,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function ChatPanel({ sessionId, onMemoryUpdate, onResetRef }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (onResetRef) {
      onResetRef.current = () => setMessages([]);
    }
  }, [onResetRef]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text, id: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat`, {
        message: text,
        session_id: sessionId,
      });

      const agentMsg = {
        role: "agent",
        content: res.data.response,
        citations: res.data.citations || [],
        thoughts: res.data.thoughts || [],
        memory_updates: res.data.memory_updates || [],
        id: Date.now() + 1,
      };

      setMessages((prev) => [...prev, agentMsg]);

      if (res.data.memory_updates?.length > 0) {
        onMemoryUpdate(res.data.memory_updates);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: "Something went wrong. Please try again.",
          citations: [],
          thoughts: [],
          id: Date.now() + 1,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStepIcon = (step) => {
    const s = step.toLowerCase();
    if (s.includes("search") || s.includes("document")) return <FileSearch className="w-3.5 h-3.5" strokeWidth={1.5} />;
    if (s.includes("weather")) return <CloudSun className="w-3.5 h-3.5" strokeWidth={1.5} />;
    if (s.includes("memory")) return <Brain className="w-3.5 h-3.5" strokeWidth={1.5} />;
    return <Sparkles className="w-3.5 h-3.5" strokeWidth={1.5} />;
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center mb-4 shadow-sm">
              <Sparkles className="w-8 h-8 text-blue-600" strokeWidth={1.5} />
            </div>
            <h2 className="font-heading text-xl font-bold text-slate-800 mb-1">
              Ask anything about your docs
            </h2>
            <p className="text-sm text-slate-500 max-w-sm">
              Upload documents, then ask questions. I'll search your files, cite sources, and remember important facts.
            </p>
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {[
                "What are the main topics in my docs?",
                "Weather in Tokyo today",
                "Summarize my uploaded files",
              ].map((q) => (
                <button
                  key={q}
                  data-testid={`suggestion-${q.slice(0, 15).replace(/\s/g, "-")}`}
                  onClick={() => {
                    setInput(q);
                    inputRef.current?.focus();
                  }}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-full hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50/50 transition-colors duration-200"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4 max-w-3xl mx-auto">
          {messages.map((msg) => (
            <div
              key={msg.id}
              data-testid={`message-${msg.role}-${msg.id}`}
              className={`flex gap-3 animate-fade-in-up ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "agent" && (
                <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center mt-1">
                  <Sparkles className="w-4 h-4 text-white" strokeWidth={1.5} />
                </div>
              )}

              <div
                className={`max-w-[80%] ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3"
                    : "bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm"
                }`}
              >
                {msg.role === "user" ? (
                  <p className="text-sm">{msg.content}</p>
                ) : (
                  <div>
                    {/* Thought Trace */}
                    {msg.thoughts && msg.thoughts.length > 0 && (
                      <Accordion type="single" collapsible className="mb-2">
                        <AccordionItem value="thoughts" className="border-none">
                          <AccordionTrigger
                            data-testid={`thought-trace-${msg.id}`}
                            className="py-1.5 px-2 -mx-1 rounded-md hover:bg-indigo-50/60 hover:no-underline text-xs"
                          >
                            <span className="flex items-center gap-1.5 text-indigo-600 font-medium">
                              <ChevronRight className="w-3 h-3" strokeWidth={2} />
                              Reasoning ({msg.thoughts.length} steps)
                            </span>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="space-y-1.5 mt-1">
                              {msg.thoughts.map((t, i) => (
                                <div
                                  key={i}
                                  className="flex items-start gap-2 border-l-2 border-indigo-200 bg-indigo-50/40 pl-3 py-1.5 rounded-r-md"
                                >
                                  <span className="text-indigo-500 mt-0.5 flex-shrink-0">
                                    {getStepIcon(t.step)}
                                  </span>
                                  <div>
                                    <p className="text-xs font-semibold text-indigo-700">
                                      {t.step}
                                    </p>
                                    <p className="text-xs text-indigo-600/80">
                                      {t.detail}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      </Accordion>
                    )}

                    {/* Response content */}
                    <div className="markdown-content text-sm">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({ node, inline, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || "");
                            return !inline && match ? (
                              <SyntaxHighlighter
                                style={oneLight}
                                language={match[1]}
                                PreTag="div"
                                customStyle={{
                                  margin: "0.5rem 0",
                                  borderRadius: "0.5rem",
                                  fontSize: "0.8rem",
                                }}
                                {...props}
                              >
                                {String(children).replace(/\n$/, "")}
                              </SyntaxHighlighter>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-slate-100">
                        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                          Sources
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((c, i) => (
                            <Tooltip key={i}>
                              <TooltipTrigger asChild>
                                <button
                                  data-testid={`citation-${msg.id}-${i}`}
                                  className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-blue-600 bg-blue-50 rounded-full border border-blue-200 hover:bg-blue-100 transition-colors duration-200 cursor-pointer"
                                >
                                  <FileSearch className="w-3 h-3" strokeWidth={1.5} />
                                  {c.source}: Page {c.page}
                                </button>
                              </TooltipTrigger>
                              <TooltipContent
                                side="bottom"
                                className="max-w-xs text-xs"
                              >
                                {c.chunk}
                              </TooltipContent>
                            </Tooltip>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Copy button */}
                    <div className="flex justify-end mt-1">
                      <button
                        data-testid={`copy-msg-${msg.id}`}
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors duration-200"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-500" strokeWidth={1.5} />
                        ) : (
                          <Copy className="w-3.5 h-3.5" strokeWidth={1.5} />
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {msg.role === "user" && (
                <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-slate-200 flex items-center justify-center mt-1">
                  <User className="w-4 h-4 text-slate-600" strokeWidth={1.5} />
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="flex gap-3 justify-start animate-fade-in-up" data-testid="chat-loading">
              <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center mt-1">
                <Sparkles className="w-4 h-4 text-white" strokeWidth={1.5} />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 text-blue-600 animate-spin" strokeWidth={1.5} />
                  <span className="text-sm text-slate-500">Thinking</span>
                  <span className="flex gap-0.5">
                    <span className="w-1 h-1 rounded-full bg-slate-400 typing-dot" />
                    <span className="w-1 h-1 rounded-full bg-slate-400 typing-dot" />
                    <span className="w-1 h-1 rounded-full bg-slate-400 typing-dot" />
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 px-6 pb-4 pt-2">
        <div
          className="max-w-3xl mx-auto flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-4 py-2 shadow-sm chat-input-glow transition-all duration-200"
        >
          <input
            ref={inputRef}
            data-testid="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Ask about your documents, weather, or anything..."
            className="flex-1 bg-transparent text-sm text-slate-800 placeholder:text-slate-400 outline-none"
            disabled={loading}
          />
          <button
            data-testid="chat-send-btn"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className={`p-2 rounded-lg transition-all duration-200 ${
              input.trim() && !loading
                ? "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
                : "bg-slate-100 text-slate-400 cursor-not-allowed"
            }`}
          >
            <Send className="w-4 h-4" strokeWidth={1.5} />
          </button>
        </div>
        <p className="text-center text-[10px] text-slate-400 mt-2">
          Powered by Gemini 2.5 Flash | Open-Meteo for weather
        </p>
      </div>
    </div>
  );
}
