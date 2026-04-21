import { BrainCircuit, User, FileText, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { useState } from "react";

interface Citation {
  page: number;
  docId: string;
  docName: string;
}

interface ChatMessageProps {
  role: "user" | "ai";
  content: string;
  sources?: Citation[];
}

export default function ChatMessage({ role, content, sources }: ChatMessageProps) {
  const isAI = role === "ai";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSourceClick = (source: Citation) => {
    // Navigate to documents page and highlight the specific document
    window.location.href = `/documents?highlight=${source.docId}&page=${source.page}`;
  };

  return (
    <div className={`px-4 py-6 md:px-6 w-full ${isAI ? 'bg-transparent' : 'bg-transparent'}`}>
      <div className="max-w-4xl mx-auto flex gap-4 md:gap-6">
        {/* Avatar */}
        <div className="flex-shrink-0">
          {isAI ? (
            <div className="w-8 h-8 rounded-full bg-[var(--color-primary)] flex items-center justify-center shadow-sm">
              <BrainCircuit className="w-5 h-5 text-white" />
            </div>
          ) : (
            <div className="w-8 h-8 rounded-full bg-[var(--color-muted)] flex items-center justify-center border border-[var(--color-border)] shadow-sm">
              <User className="w-5 h-5 text-[var(--color-muted-foreground)]" />
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 space-y-4 overflow-hidden pt-1 relative group">
          {isAI && (
            <button
              onClick={handleCopy}
              className="absolute top-0 right-0 p-1.5 text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] hover:bg-[var(--color-muted)] rounded-md opacity-0 group-hover:opacity-100 transition-opacity z-10"
              title="Copy to clipboard"
            >
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
            </button>
          )}
          <div className="text-[var(--color-foreground)] pr-8">
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
              components={{
                h1: ({node, ...props}) => <h1 className="text-2xl font-extrabold mt-6 mb-4 text-[var(--color-primary)] border-b pb-2 border-[var(--color-border)] leading-tight" {...props} />,
                h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-5 mb-3 text-[var(--color-foreground)] leading-snug" {...props} />,
                h3: ({node, ...props}) => <h3 className="text-lg font-semibold mt-4 mb-2 text-[var(--color-foreground)]" {...props} />,
                ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-4 space-y-1.5" {...props} />,
                ol: ({node, ...props}) => <ol className="list-decimal pl-6 mb-4 space-y-1.5" {...props} />,
                li: ({node, ...props}) => <li className="leading-relaxed marker:text-[var(--color-primary)] marker:font-bold" {...props} />,
                p: ({node, ...props}) => <p className="mb-4 leading-relaxed" {...props} />,
                strong: ({node, ...props}) => <strong className="font-bold text-[var(--color-primary)]" {...props} />,
                em: ({node, ...props}) => <em className="italic text-[var(--color-muted-foreground)]" {...props} />,
                code: ({node, ...props}) => <code className="px-1.5 py-0.5 rounded bg-[var(--color-muted)] text-[var(--color-primary)] font-mono text-sm" {...props} />,
              }}
            >
              {content}
            </ReactMarkdown>
          </div>

          {/* Sources Section */}
          {sources && sources.length > 0 && (
            <div className="mt-4 pt-3">
              <p className="text-xs font-medium text-[var(--color-muted-foreground)] mb-2">Sources:</p>
              <div className="flex flex-wrap gap-2">
                {sources.map((source, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSourceClick(source)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-[var(--color-muted)] text-[var(--color-muted-foreground)] border border-[var(--color-border)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)] cursor-pointer transition-colors"
                    title={`View page ${source.page} of ${source.docName}`}
                  >
                    <FileText className="w-3 h-3 opacity-70" />
                    <span className="opacity-70">Pg {source.page}</span>
                    <span className="w-px h-3 bg-[var(--color-border)]"></span>
                    <span className="truncate max-w-[150px]">{source.docName}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
