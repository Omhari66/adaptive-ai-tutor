const getApiBase = () => {
  if (typeof window !== "undefined" && window.location.hostname !== "localhost") {
    return `http://${window.location.hostname}:8000/api`;
  }
  return "http://127.0.0.1:8000/api";
};
const API_BASE = getApiBase();

function getAuthHeaders(): { [key: string]: string } {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

// Types
export interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  status: string;
  pages: number;
  dateAdded: string;
}

export interface ChatSession {
  id: string;
  title: string;
  time: string;
  is_pinned?: boolean;
}

export interface Source {
  page: number;
  docId: string;
  docName: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  sources?: Source[];
}

export interface QuizQuestion {
  id?: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation?: string;
}

// Documents
export async function getDocuments(): Promise<Document[]> {
  const res = await fetch(`${API_BASE}/documents`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Failed to fetch documents");
  const data = await res.json();
  return data.documents;
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function deleteDocument(docId: string) {
  const res = await fetch(`${API_BASE}/documents/${docId}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
}

// Chat
export async function getChatSessions(): Promise<ChatSession[]> {
  const res = await fetch(`${API_BASE}/chat/sessions`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Failed to fetch sessions");
  const data = await res.json();
  return data.sessions;
}

export async function updateChatSession(sessionId: string, data: { title?: string, is_pinned?: boolean }) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Update failed");
  return res.json();
}

export async function deleteChatSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Delete failed");
  return res.json();
}

export async function getChatMessages(sessionId: string): Promise<ChatMessage[]> {
  const res = await fetch(`${API_BASE}/chat/${sessionId}/messages`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Failed to fetch messages");
  const data = await res.json();
  return data.messages;
}

export async function sendChatMessage(query: string, documentIds?: string[], sessionId?: string) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ query, documentIds, sessionId }),
  });
  if (!res.ok) throw new Error("Chat failed");
  return res.json();
}

// To implement SSE stream, you use standard browser EventSource or custom fetch reader in the UI component, not here.

// Quiz
export async function generateQuiz(documentIds?: string[], numQuestions = 5): Promise<{ quizId: string, title: string, questions: QuizQuestion[] }> {
  // Use POST to pass parameters robustly
  const res = await fetch(`${API_BASE}/quiz/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ documentIds, numQuestions }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Quiz generation failed");
  }
  return res.json();
}

export async function submitQuiz(quizId: string, answers: number[]): Promise<any> {
  const res = await fetch(`${API_BASE}/quiz/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ quizId, answers }),
  });
  if (!res.ok) throw new Error("Quiz submission failed");
  return res.json();
}

// Progress
export async function getProgress() {
  const res = await fetch(`${API_BASE}/progress`, {
    headers: { ...getAuthHeaders() }
  });
  if (!res.ok) throw new Error("Failed to fetch progress");
  return res.json();
}

// Auth
export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Login failed");
  }
  return res.json();
}

export async function registerUser(email: string, password: string, name: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Registration failed");
  }
  return res.json();
}
