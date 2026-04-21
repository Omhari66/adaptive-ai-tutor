"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { MessageSquare, Files, BrainCircuit, BarChart3, Settings, PlusCircle, LogOut, MoreVertical, Edit2, Pin, Trash2, Share2, Check, X } from "lucide-react";
import { getChatSessions, ChatSession, deleteChatSession, updateChatSession } from "@/lib/api";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  const fetchSessions = () => {
    getChatSessions().then(setSessions).catch(console.error);
  };

  useEffect(() => {
    fetchSessions();
  }, [pathname]); // Refresh on navigation

  const handleRename = async (e: React.FormEvent, id: string) => {
    e.preventDefault();
    if (!editTitle.trim()) {
      setEditingId(null);
      return;
    }
    try {
      await updateChatSession(id, { title: editTitle });
      fetchSessions();
    } catch(err) {
      console.error(err);
    }
    setEditingId(null);
  };

  const handlePinToggle = async (e: React.MouseEvent, id: string, currentPin: boolean) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await updateChatSession(id, { is_pinned: !currentPin });
      fetchSessions();
    } catch(err) {
      console.error(err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat?")) return;
    try {
      await deleteChatSession(id);
      if (pathname === '/chat' && window.location.search.includes(id)) {
        router.push('/chat');
      }
      fetchSessions();
    } catch(err) {
      console.error(err);
    }
  };

  const handleShare = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    const shareUrl = `${window.location.origin}/chat?id=${id}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      alert("Chat link copied to clipboard!");
    } catch (err) {
      console.error("Failed to copy", err);
    }
  };

  const pinnedSessions = sessions.filter(s => s.is_pinned);
  const recentSessions = sessions.filter(s => !s.is_pinned);

  const renderChatItem = (chat: ChatSession) => {
    const isEditing = editingId === chat.id;

    return (
      <div key={chat.id} className="relative group">
        {isEditing ? (
          <form onSubmit={(e) => handleRename(e, chat.id)} className="mx-2 px-2 py-1 flex items-center gap-1 bg-[var(--color-background)] rounded-md border border-[var(--color-primary)]">
            <input 
              autoFocus
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="flex-1 bg-transparent w-full text-sm outline-none text-[var(--color-foreground)]"
            />
            <button type="submit" className="text-emerald-500 p-1 hover:bg-emerald-500/10 rounded">
              <Check className="w-3 h-3" />
            </button>
            <button type="button" onClick={() => setEditingId(null)} className="text-red-500 p-1 hover:bg-red-500/10 rounded">
              <X className="w-3 h-3" />
            </button>
          </form>
        ) : (
          <Link href={`/chat?id=${chat.id}`}>
            <div className="flex items-center justify-between px-3 py-2 mx-1 text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-[var(--color-sidebar-hover)] rounded-md transition-colors">
              <span className="truncate pr-4">{chat.title}</span>
              <div className="hidden group-hover:flex items-center gap-0.5 absolute right-2 bg-[var(--color-sidebar-hover)] pl-1 rounded pointer-events-auto">
                <button onClick={(e) => handlePinToggle(e, chat.id, !!chat.is_pinned)} className="p-1.5 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] rounded transition-colors" title={chat.is_pinned ? "Unpin" : "Pin"}>
                  <Pin className={`w-3.5 h-3.5 ${chat.is_pinned ? "fill-current" : ""}`} />
                </button>
                <button 
                  onClick={(e) => { 
                    e.preventDefault(); 
                    e.stopPropagation(); 
                    setEditingId(chat.id); 
                    setEditTitle(chat.title); 
                  }} 
                  className="p-1.5 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] rounded transition-colors" title="Rename">
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button onClick={(e) => handleShare(e, chat.id)} className="p-1.5 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] rounded transition-colors" title="Share">
                  <Share2 className="w-3.5 h-3.5" />
                </button>
                <button onClick={(e) => handleDelete(e, chat.id)} className="p-1.5 text-[var(--color-muted-foreground)] hover:text-red-500 rounded transition-colors" title="Delete">
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </Link>
        )}
      </div>
    );
  };

  const handleNewChat = () => {
    // Navigate to chat page without a session ID
    router.push("/chat");
  };

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    router.push("/login");
  };

  const navItems = [
    { name: "Chat", icon: MessageSquare, path: "/chat" },
    { name: "Documents", icon: Files, path: "/documents" },
    { name: "Quizzes", icon: BrainCircuit, path: "/quiz" },
    { name: "Progress", icon: BarChart3, path: "/progress" },
  ];

  return (
    <div className="w-64 h-screen bg-[var(--color-sidebar)] border-r border-[var(--color-sidebar-border)] flex flex-col p-4">
      {/* Brand */}
      <div className="flex items-center gap-2 mb-8 px-2 py-2">
        <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 rounded-lg bg-[var(--color-primary)] flex items-center justify-center">
            <BrainCircuit className="w-5 h-5 text-white" />
          </div>
          <span className="font-semibold text-[var(--color-sidebar-foreground)] tracking-tight">Study Assistant</span>
        </Link>
      </div>

      {/* New Chat Button */}
      <button onClick={handleNewChat} className="flex items-center gap-2 w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-md px-3 py-2 mb-6 text-sm font-medium hover:bg-[var(--color-muted)] transition-colors cursor-pointer">
        <PlusCircle className="w-4 h-4" />
        New Chat
      </button>

      {/* Main Nav */}
      <nav className="flex-1 overflow-y-auto">
        <div className="space-y-1 mb-8">
          {navItems.map((item) => {
            const isActive = pathname === item.path || (pathname === '/' && item.path === '/chat');
            return (
              <Link key={item.name} href={item.path}>
                <div className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                  isActive 
                    ? "bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]" 
                    : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]"
                }`}>
                  <item.icon className="w-4 h-4" />
                  {item.name}
                </div>
              </Link>
            );
          })}
        </div>

        {/* Pinned Chats Section */}
        {pinnedSessions.length > 0 && (
          <>
            <div className="px-2 mb-2 mt-4">
              <span className="text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider flex items-center gap-1 px-1">
                <Pin className="w-3 h-3" /> Pinned
              </span>
            </div>
            <div className="space-y-0.5">
              {pinnedSessions.map(renderChatItem)}
            </div>
          </>
        )}

        {/* Recent Chats Section */}
        <div className="px-2 mb-2 mt-4">
          <span className="text-xs font-semibold text-[var(--color-muted-foreground)] uppercase tracking-wider px-1">Recent</span>
        </div>
        <div className="space-y-0.5">
          {recentSessions.map(renderChatItem)}
        </div>
      </nav>

      {/* Footer */}
      <div className="pt-4 mt-auto border-t border-[var(--color-sidebar-border)] space-y-1">
        <Link href="/settings">
          <div className={`flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors ${
            pathname === '/settings'
              ? "bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]" 
              : "text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]"
          }`}>
            <Settings className="w-4 h-4" />
            Settings
          </div>
        </Link>
        <button onClick={handleLogout} className="flex items-center gap-3 w-full px-3 py-2 rounded-md text-sm font-medium text-red-500/80 hover:bg-red-500/10 hover:text-red-500 transition-colors">
          <LogOut className="w-4 h-4" />
          Log Out
        </button>
      </div>
    </div>
  );
}
