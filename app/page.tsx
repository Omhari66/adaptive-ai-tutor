"use client";

import { useEffect, useState } from "react";
import { FileText, MessageSquare, ArrowRight, UploadCloud } from "lucide-react";
import Link from "next/link";
import { getDocuments, getChatSessions, Document, ChatSession } from "@/lib/api";

export default function DashboardPage() {
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [recentChats, setRecentChats] = useState<ChatSession[]>([]);

  useEffect(() => {
    getDocuments()
      .then(docs => setRecentDocs(docs.slice(0, 3)))
      .catch(console.error);
    getChatSessions()
      .then(chats => setRecentChats(chats.slice(0, 3)))
      .catch(console.error);
  }, []);

  return (
    <div className="p-8 max-w-6xl mx-auto w-full">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-[var(--color-foreground)] tracking-tight mb-2">Welcome back, Student</h1>
        <p className="text-[var(--color-muted-foreground)] text-lg">Ready to master your subjects today?</p>
      </header>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
        <Link href="/documents">
          <div className="group flex items-center justify-between p-6 bg-[var(--color-primary)] text-white rounded-2xl shadow-sm hover:shadow-md transition-all cursor-pointer">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/20 rounded-xl">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <h2 className="font-semibold text-lg">Upload Material</h2>
                <p className="text-white/80 text-sm">PDF, DOCX, Notes</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 opacity-70 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </div>
        </Link>
        <Link href="/chat">
          <div className="group flex items-center justify-between p-6 bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl shadow-sm hover:border-[var(--color-primary)] transition-all cursor-pointer">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-[var(--color-muted)] text-[var(--color-primary)] rounded-xl">
                <MessageSquare className="w-6 h-6" />
              </div>
              <div>
                <h2 className="font-semibold text-lg text-[var(--color-foreground)]">Start New Chat</h2>
                <p className="text-[var(--color-muted-foreground)] text-sm">Ask questions based on your files</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-[var(--color-primary)] opacity-70 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Documents Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-[var(--color-foreground)]">Recent Documents</h3>
            <Link href="/documents" className="text-sm font-medium text-[var(--color-primary)] hover:underline">View All</Link>
          </div>
          <div className="bg-[var(--color-card)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
             {recentDocs.length === 0 ? (
                <div className="p-4 text-center text-sm text-[var(--color-muted-foreground)] border-b border-[var(--color-border)]">
                  No documents uploaded yet.
                </div>
             ) : (
                recentDocs.map((doc, idx) => (
                  <Link key={doc.id} href={`/chat?documentId=${doc.id}`}>
                    <div className={`flex items-center justify-between p-4 hover:bg-[var(--color-sidebar-hover)] transition-colors cursor-pointer ${idx !== recentDocs.length - 1 ? 'border-b border-[var(--color-border)]' : ''}`}>
                      <div className="flex items-center gap-3 overflow-hidden">
                        <div className="p-2 bg-[var(--color-muted)] rounded-lg shrink-0">
                          <FileText className="w-4 h-4 text-[var(--color-muted-foreground)]" />
                        </div>
                        <div className="truncate">
                          <p className="text-sm font-medium text-[var(--color-foreground)] truncate">{doc.name}</p>
                          <p className="text-xs text-[var(--color-muted-foreground)]">{doc.dateAdded} • {doc.size}</p>
                        </div>
                      </div>
                      <div className="shrink-0 ml-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${
                          doc.status === 'ready' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400'
                        }`}>
                          {doc.status === 'ready' ? 'Ready' : 'Processing'}
                        </span>
                      </div>
                    </div>
                  </Link>
                ))
             )}
          </div>
        </section>

        {/* Recent Chats Section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-[var(--color-foreground)]">Recent Chats</h3>
            <Link href="/chat" className="text-sm font-medium text-[var(--color-primary)] hover:underline">View History</Link>
          </div>
          <div className="bg-[var(--color-card)] rounded-2xl border border-[var(--color-border)] overflow-hidden">
            {recentChats.length === 0 ? (
                <div className="p-4 text-center text-sm text-[var(--color-muted-foreground)]">
                  No recent chats found.
                </div>
            ) : (
              recentChats.map((chat, idx) => (
                <Link key={chat.id} href={`/chat?id=${chat.id}`}>
                  <div className={`flex items-center justify-between p-4 hover:bg-[var(--color-sidebar-hover)] transition-colors cursor-pointer ${idx !== recentChats.length - 1 ? 'border-b border-[var(--color-border)]' : ''}`}>
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="p-2 bg-[var(--color-primary)]/10 rounded-lg shrink-0">
                        <MessageSquare className="w-4 h-4 text-[var(--color-primary)]" />
                      </div>
                      <div className="truncate">
                        <p className="text-sm font-medium text-[var(--color-foreground)] truncate">{chat.title}</p>
                        <p className="text-xs text-[var(--color-muted-foreground)]">{chat.time}</p>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[var(--color-muted-foreground)] shrink-0 ml-4" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
