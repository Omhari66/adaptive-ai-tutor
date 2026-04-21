"use client";

import { Send, Paperclip, Sparkles } from "lucide-react";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  onUploadComplete?: (docId: string, fileName: string) => void;
  disabled?: boolean;
  mode?: string;
}

export default function ChatInput({ onSendMessage, onUploadComplete, disabled, mode = "NORMAL" }: ChatInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [input, setInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSendMessage(input);
    setInput("");
  };

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const { uploadDocument } = await import("@/lib/api");
      const res = await uploadDocument(file);
      if (onUploadComplete && res.docId) {
        onUploadComplete(res.docId, file.name);
      }
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to upload document");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const promptsByMode: Record<string, { label: string, text: string }[]> = {
    NORMAL: [
      { label: "Plan Day", text: "Hey! Can you help me plan my day practically?" },
      { label: "Release Stress", text: "I'm feeling a bit stressed. Can we chat to clear my mind?" },
      { label: "Fun Fact", text: "Tell me something fun to lighten the mood! 😊" },
      { label: "Study Routine", text: "Let's create a solid, non-overwhelming study routine." },
    ],
    TEACHER: [
      { label: "Explain Again", text: "Explain this again differently." },
      { label: "Key Points", text: "What are the most important key points?" },
      { label: "Test Me", text: "Ask me a question to test my knowledge." },
      { label: "Mistakes", text: "What are common mistakes students make here?" },
    ],
    REVISION: [
      { label: "Short Notes", text: "Give me ultra short notes on this." },
      { label: "Formula Sheet", text: "Create a formula or fact sheet for this." },
      { label: "Memory Tricks", text: "Give me a memory trick to remember this." },
      { label: "Weak Areas", text: "Help me review my weak areas on this topic." },
    ],
    EXAM: [
      { label: "Start Quiz", text: "Start a quiz on this material." },
      { label: "Steps", text: "Show me the solution steps for these problems." },
      { label: "Exam Tricks", text: "Do you have any exam tricks or hacks?" },
      { label: "Most Asked", text: "What are the most frequently asked questions?" },
    ]
  };

  const suggestedPrompts = promptsByMode[mode] || promptsByMode["NORMAL"];

  return (
    <div className="relative w-full max-w-4xl mx-auto px-4 md:px-6 pb-6 pt-2">
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt"
        onChange={handleFileChange}
        disabled={isUploading}
      />

      <div className="flex gap-2 mb-3 px-1 overflow-x-auto no-scrollbar">
        {suggestedPrompts.map((prompt) => (
          <button
            key={prompt.label}
            onClick={() => setInput(prompt.text)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-[var(--color-background)] border border-[var(--color-border)] rounded-full text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-[var(--color-muted)] transition-colors whitespace-nowrap"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {prompt.label}
          </button>
        ))}
      </div>

      <div className="relative flex items-end w-full bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl shadow-sm focus-within:ring-1 focus-within:ring-[var(--color-primary)] focus-within:border-[var(--color-primary)] transition-all">
        {/* Attachment Button */}
        <button
          onClick={handleAttachmentClick}
          disabled={isUploading}
          className="p-3 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors rounded-l-2xl disabled:opacity-50 cursor-pointer"
          aria-label="Attach Document"
          title="Upload a document"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        {/* Dynamic Textarea */}
        <textarea
          placeholder="Ask a question about your documents..."
          className="w-full max-h-[200px] min-h-[56px] py-3.5 px-2 bg-transparent border-none focus:outline-none resize-none text-[var(--color-foreground)] text-sm md:text-base leading-relaxed placeholder:text-[var(--color-muted-foreground)] no-scrollbar"
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          disabled={disabled || isUploading}
        />

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled || isUploading}
          className="p-2 m-2 h-10 w-10 flex items-center justify-center bg-[var(--color-primary)] text-white rounded-xl shadow hover:bg-[var(--color-primary)]/90 transition-colors disabled:opacity-50"
          aria-label="Send Message"
        >
          <Send className="w-5 h-5 ml-0.5" />
        </button>
      </div>

      <div className="mt-3 text-center">
        <p className="text-xs text-[var(--color-muted-foreground)]">
          AI Study Assistant relies on your documents. Double-check important facts.
        </p>
      </div>
    </div>
  );
}
