"use client";

import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import { useEffect, useRef, useState, Suspense } from "react";
import { ChatMessage as MessageType, Source } from "@/lib/api";
import { useSearchParams, useRouter } from "next/navigation";
import { BrainCircuit, GraduationCap, Repeat, Target, ChevronDown } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

function ChatContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<MessageType[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<{id: string, name: string}[]>([]);
  
  // Adaptive Tutor State
  const [mode, setMode] = useState<string>("NORMAL");
  const [topic, setTopic] = useState<string | null>(null);
  const [suggestMode, setSuggestMode] = useState<string | null>(null);
  const [confidenceScore, setConfidenceScore] = useState<number | null>(null);

  // Sync URL params with state on mount and url changes
  useEffect(() => {
    const urlSessionId = searchParams.get("sessionId") || searchParams.get("id");
    
    if (urlSessionId && urlSessionId !== sessionId) {
      setSessionId(urlSessionId);
      
      const fetchMessages = async () => {
        try {
          const { getChatMessages } = await import("@/lib/api");
          const msgs = await getChatMessages(urlSessionId);
          if (msgs && msgs.length > 0) {
            setMessages(msgs);
          } else {
            setMessages([]);
          }
        } catch (e) {
          console.error("Failed to load chat history:", e);
        }
      };
      fetchMessages();
    } else if (!urlSessionId && sessionId) {
      // "New Chat" clicked
      setSessionId(undefined);
      setMessages([]);
    }
    
    const urlDocId = searchParams.get("documentId");
    if (urlDocId && !hasInitialized) {
      const fetchDocs = async () => {
         const { getDocuments } = await import("@/lib/api");
         const docs = await getDocuments();
         const target = docs.find(d => d.id === urlDocId);
         if (target) {
            setSelectedDocs([{ id: target.id, name: target.name }]);
         }
      };
      fetchDocs();
      setHasInitialized(true);
    }
  }, [searchParams, sessionId, hasInitialized]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    // 1. Add User Message
    const userMsgId = Date.now().toString();
    setMessages(prev => [...prev, { id: userMsgId, role: "user", content }]);
    setIsGenerating(true);

    // 2. Add Empty AI Message block
    const aiMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: aiMsgId, role: "ai", content: "", sources: [] }]);

    try {
      // 3. Setup fetch request with SSE header
      const payload: any = { query: content, sessionId, mode };
      if (selectedDocs.length > 0) {
        payload.documentIds = selectedDocs.map(d => d.id);
      }
      
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
          "Authorization": `Bearer ${localStorage.getItem("auth_token") || ""}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let completeResponse = "";
      let returnedSessionId: string | undefined = undefined;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Split chunk by lines since SSE sends "data: {...}\n\n"
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.substring(6);
            if (dataStr === "[DONE]") break;

            try {
              const data = JSON.parse(dataStr);
              if (data.type === "text") {
                completeResponse += data.content;
                // Update the AI message linearly
                setMessages(prev => prev.map(msg =>
                  msg.id === aiMsgId ? { ...msg, content: completeResponse } : msg
                ));
              } else if (data.type === "sources") {
                setMessages(prev => prev.map(msg =>
                  msg.id === aiMsgId ? { ...msg, sources: data.sources } : msg
                ));
              } else if (data.type === "session") {
                // Capture session ID from backend for URL sync
                returnedSessionId = data.sessionId;
              } else if (data.type === "topic") {
                setTopic(data.topic);
              } else if (data.type === "suggest_mode") {
                setSuggestMode(data.suggest_mode);
              } else if (data.type === "confidence_score") {
                setConfidenceScore(data.confidence_score);
              } else if (data.type === "done") {
                // Done parsing
              }
            } catch (e) {
               // Incomplete JSON chunk, skip
            }
          }
        }
      }

      // Update URL with session ID if this is a new session
      if (returnedSessionId && !sessionId) {
        setSessionId(returnedSessionId);
        router.replace(`?sessionId=${returnedSessionId}`, { scroll: false });
      }
    } catch (error) {
       console.error("Chat Error:", error);
       setMessages(prev => prev.map(msg =>
         msg.id === aiMsgId ? { ...msg, content: "Sorry, I encountered an error retrieving that information." } : msg
       ));
    } finally {
      setIsGenerating(false);
    }
  };

  const modeDetails: Record<string, { bg: string, border: string, text: string, icon: any, label: string }> = {
    NORMAL: { bg: "bg-[var(--color-background)]", border: "border-[var(--color-border)]", text: "text-[var(--color-foreground)]", icon: BrainCircuit, label: "Exploration" },
    TEACHER: { bg: "bg-blue-500/5", border: "border-blue-500/20", text: "text-blue-500", icon: GraduationCap, label: "Core Learning" },
    REVISION: { bg: "bg-purple-500/5", border: "border-purple-500/20", text: "text-purple-500", icon: Repeat, label: "Memory + Compression" },
    EXAM: { bg: "bg-orange-500/5", border: "border-orange-500/20", text: "text-orange-500", icon: Target, label: "Performance Testing" }
  };

  const currMode = modeDetails[mode] || modeDetails["NORMAL"];
  const ModeIcon = currMode.icon;

  return (
    <div className="flex flex-col h-full w-full bg-[var(--color-background)]">
      <header className={`sticky top-0 z-10 flex items-center justify-between pl-14 pr-6 h-16 ${currMode.bg} backdrop-blur-md border-b ${currMode.border} transition-colors duration-300`}>
        <div className="flex items-center gap-4">
          <div className="flex flex-col">
            <h1 className="font-semibold text-lg text-[var(--color-foreground)] leading-tight">AI Tutor</h1>
            <span className={`text-xs font-medium flex items-center gap-1 ${currMode.text}`}>
               <ModeIcon size={12} /> {currMode.label}
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-2">
            <span className="text-xs text-[var(--color-muted-foreground)] font-medium">Mode:</span>
            <select 
              value={mode} 
              onChange={(e) => setMode(e.target.value)}
              className="text-sm bg-[var(--color-muted)] text-[var(--color-foreground)] border border-[var(--color-border)] rounded-md px-2 py-1 outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            >
              <option value="NORMAL">Normal</option>
              <option value="TEACHER">Teacher</option>
              <option value="REVISION">Revision</option>
              <option value="EXAM">Exam</option>
            </select>
          </div>
        </div>
        
        {topic && (
          <div className="text-xs font-medium px-2 py-1 bg-green-500/10 text-green-500 rounded border border-green-500/20">
            {topic}
          </div>
        )}
      </header>

      {(suggestMode || confidenceScore !== null) && (
        <div className="w-full bg-[var(--color-primary)]/10 border-b border-[var(--color-primary)]/20 px-6 py-2 flex items-center justify-between shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-6 text-sm">
            {confidenceScore !== null && (
              <span className="font-medium text-[var(--color-foreground)]">
                Proficiency: <span className={confidenceScore < 0.4 ? "text-red-500" : "text-green-500"}>{(confidenceScore * 100).toFixed(0)}%</span>
              </span>
            )}
            {suggestMode && (
              <span className="text-[var(--color-muted-foreground)]">
                 System Suggests: <strong className="text-[var(--color-primary)]">{suggestMode} mode</strong>
              </span>
            )}
          </div>
          {suggestMode && suggestMode !== mode && (
            <button 
              onClick={() => { setMode(suggestMode); setSuggestMode(null); }}
              className="px-3 py-1 bg-[var(--color-primary)] text-[var(--color-primary-foreground)] rounded text-xs font-semibold hover:opacity-90 transition-opacity"
            >
              Switch Mode
            </button>
          )}
        </div>
      )}
      
      <div ref={scrollRef} className="flex-1 overflow-y-auto no-scrollbar pb-4">
        <div className="flex flex-col">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full min-h-[300px] text-[var(--color-muted-foreground)]">
              Ask anything about your study materials. I will scan them and provide answers with citations!
            </div>
          )}
          {messages.map((msg) => (
            <ChatMessage 
              key={msg.id} 
              role={msg.role} 
              content={msg.content} 
              sources={msg.sources} 
            />
          ))}
        </div>
        <div className="h-4"></div>
      </div>

      <div className="pt-2 bg-gradient-to-t from-[var(--color-background)] via-[var(--color-background)] to-transparent shrink-0">
        {selectedDocs.length > 0 && (
          <div className="flex flex-wrap gap-2 px-6 pb-2 max-w-4xl mx-auto">
            <span className="text-xs text-[var(--color-muted-foreground)] font-medium flex items-center mr-1">Context:</span>
            {selectedDocs.map(doc => (
              <div key={doc.id} className="flex items-center gap-1.5 px-3 py-1 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-full text-xs font-semibold">
                 <span>{doc.name}</span>
                 <button 
                  onClick={() => setSelectedDocs(prev => prev.filter(d => d.id !== doc.id))} 
                  className="hover:text-red-500 rounded-full w-4 h-4 flex items-center justify-center transition-colors"
                  aria-label="Remove context"
                 >
                   ×
                 </button>
              </div>
            ))}
          </div>
        )}
        <ChatInput 
          onSendMessage={handleSendMessage} 
          disabled={isGenerating} 
          onUploadComplete={(docId, fileName) => setSelectedDocs(prev => [...prev, { id: docId, name: fileName }])}
          mode={mode}
        />
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full w-full">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
