import { useState, useEffect } from "react";
import axios from "axios";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Brain,
  User,
  Building2,
  Clock,
  Sparkles,
  FileText,
  RefreshCw,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MemoryFeed({ memoryEntries }) {
  const [userMemory, setUserMemory] = useState("");
  const [companyMemory, setCompanyMemory] = useState("");
  const [activeTab, setActiveTab] = useState("feed");

  useEffect(() => {
    fetchMemoryContent();
  }, [memoryEntries]);

  const fetchMemoryContent = async () => {
    try {
      const [userRes, companyRes] = await Promise.all([
        axios.get(`${API}/memory/user`),
        axios.get(`${API}/memory/company`),
      ]);
      setUserMemory(userRes.data.content);
      setCompanyMemory(companyRes.data.content);
    } catch (e) {
      console.error("Failed to fetch memory", e);
    }
  };

  const formatTimestamp = (ts) => {
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 pt-4 pb-3 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-heading text-sm font-bold text-slate-900 tracking-tight">
              Memory Feed
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              High-signal facts extracted by the agent
            </p>
          </div>
          <button
            data-testid="refresh-memory-btn"
            onClick={fetchMemoryContent}
            className="p-1.5 rounded-md text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-colors duration-200"
          >
            <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex-1 flex flex-col overflow-hidden"
      >
        <div className="px-4 pt-3">
          <TabsList className="w-full grid grid-cols-3 h-8">
            <TabsTrigger
              data-testid="tab-feed"
              value="feed"
              className="text-xs font-medium"
            >
              <Sparkles className="w-3 h-3 mr-1" strokeWidth={1.5} />
              Feed
            </TabsTrigger>
            <TabsTrigger
              data-testid="tab-user"
              value="user"
              className="text-xs font-medium"
            >
              <User className="w-3 h-3 mr-1" strokeWidth={1.5} />
              User
            </TabsTrigger>
            <TabsTrigger
              data-testid="tab-company"
              value="company"
              className="text-xs font-medium"
            >
              <Building2 className="w-3 h-3 mr-1" strokeWidth={1.5} />
              Org
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Feed Tab */}
        <TabsContent value="feed" className="flex-1 overflow-hidden mt-0">
          <ScrollArea className="h-full px-4 pt-2">
            {memoryEntries.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Brain
                  className="w-10 h-10 text-slate-300 mb-3"
                  strokeWidth={1.5}
                />
                <p className="text-sm text-slate-400 font-medium">
                  No memories yet
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Chat with the agent to generate insights
                </p>
              </div>
            ) : (
              <div className="space-y-2 pb-4">
                {memoryEntries.map((entry, i) => (
                  <div
                    key={entry.id || i}
                    data-testid={`memory-entry-${entry.id || i}`}
                    className="p-3 bg-white border border-slate-100 rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] hover:border-blue-200 transition-all duration-200 animate-fade-in-up"
                    style={{ animationDelay: `${i * 50}ms` }}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <Badge
                        className={`text-[10px] px-1.5 py-0.5 font-semibold ${
                          entry.target === "user"
                            ? "bg-blue-50 text-blue-600 border-blue-200"
                            : "bg-amber-50 text-amber-600 border-amber-200"
                        }`}
                        variant="outline"
                      >
                        {entry.target === "user" ? (
                          <User className="w-2.5 h-2.5 mr-0.5 inline" strokeWidth={2} />
                        ) : (
                          <Building2 className="w-2.5 h-2.5 mr-0.5 inline" strokeWidth={2} />
                        )}
                        {entry.target === "user" ? "USER" : "ORG"}
                      </Badge>
                      <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                        <Clock className="w-2.5 h-2.5" strokeWidth={1.5} />
                        {formatTimestamp(entry.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {entry.fact}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </TabsContent>

        {/* User Memory Tab */}
        <TabsContent value="user" className="flex-1 overflow-hidden mt-0">
          <ScrollArea className="h-full px-4 pt-2">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-blue-500" strokeWidth={1.5} />
              <span className="text-xs font-semibold text-slate-600">
                USER_MEMORY.md
              </span>
            </div>
            {userMemory ? (
              <pre
                data-testid="user-memory-content"
                className="text-xs text-slate-600 whitespace-pre-wrap font-mono bg-slate-50 p-3 rounded-lg border border-slate-100"
              >
                {userMemory}
              </pre>
            ) : (
              <p className="text-xs text-slate-400 text-center py-8">
                No user memory recorded yet
              </p>
            )}
          </ScrollArea>
        </TabsContent>

        {/* Company Memory Tab */}
        <TabsContent value="company" className="flex-1 overflow-hidden mt-0">
          <ScrollArea className="h-full px-4 pt-2">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-amber-500" strokeWidth={1.5} />
              <span className="text-xs font-semibold text-slate-600">
                COMPANY_MEMORY.md
              </span>
            </div>
            {companyMemory ? (
              <pre
                data-testid="company-memory-content"
                className="text-xs text-slate-600 whitespace-pre-wrap font-mono bg-slate-50 p-3 rounded-lg border border-slate-100"
              >
                {companyMemory}
              </pre>
            ) : (
              <p className="text-xs text-slate-400 text-center py-8">
                No company memory recorded yet
              </p>
            )}
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}
