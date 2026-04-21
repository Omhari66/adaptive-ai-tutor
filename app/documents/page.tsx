"use client";

import { FileText, UploadCloud, File, Trash2, CheckCircle2, Clock } from "lucide-react";
import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getDocuments, uploadDocument, deleteDocument, Document } from "@/lib/api";

function DocumentsContent() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const searchParams = useSearchParams();
  const highlightDocId = searchParams.get('highlight');
  const highlightPage = searchParams.get('page');

  // Fetch documents on load and poll every 5 seconds if any are processing
  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 5000);
    return () => clearInterval(interval);
  }, []);

  // Scroll to highlighted document once loaded
  useEffect(() => {
    if (highlightDocId && documents.length > 0) {
      const el = document.getElementById(`doc-${highlightDocId}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [highlightDocId, documents]);

  const fetchDocs = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
    } catch (error) {
      console.error("Failed to fetch documents", error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await uploadDocument(file);
      await fetchDocs(); // Immediately refresh list to show "processing"
    } catch (error) {
      console.error("Upload failed", error);
      alert("Failed to upload document");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    try {
      await deleteDocument(id);
      await fetchDocs();
    } catch (error) {
      console.error("Failed to delete", error);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto w-full">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Documents</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">Upload and manage your study materials</p>
      </header>

      {/* Upload Zone */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className={`mb-10 w-full border-2 border-dashed border-[var(--color-border)] rounded-3xl p-12 flex flex-col items-center justify-center transition-colors cursor-pointer group ${isUploading ? 'bg-[var(--color-muted)] opacity-50' : 'bg-[var(--color-background)] hover:bg-[var(--color-muted)]'}`}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept=".pdf,.docx,.txt"
          onChange={handleFileUpload}
          disabled={isUploading}
        />
        <div className="p-4 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-full mb-4 group-hover:scale-110 transition-transform">
          <UploadCloud className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-medium text-[var(--color-foreground)] mb-1">
          {isUploading ? "Uploading..." : "Click or drag file to this area to upload"}
        </h3>
        <p className="text-sm text-[var(--color-muted-foreground)] text-center max-w-md">
          Support for a single or bulk upload. Only PDF, DOCX, and TXT files under 50MB are permitted.
        </p>
      </div>

      {/* Document List */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-muted-foreground)] mb-4">Your Files ({documents.length})</h3>
        <div className="grid gap-4">
          {documents.map((doc) => {
            const isHighlighted = highlightDocId === doc.id;
            return (
              <div 
                key={doc.id} 
                id={`doc-${doc.id}`}
                className={`flex items-center justify-between p-4 bg-[var(--color-card)] border rounded-2xl transition-all ${
                  isHighlighted 
                    ? 'border-[var(--color-primary)] shadow-md ring-1 ring-[var(--color-primary)] bg-[var(--color-primary)]/5' 
                    : 'border-[var(--color-border)] hover:shadow-sm'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${doc.type === 'pdf' ? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400' : 'bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400'}`}>
                    {doc.type === 'pdf' ? <FileText className="w-6 h-6" /> : <File className="w-6 h-6" />}
                  </div>
                  <div>
                    <h4 className={`font-medium text-base ${isHighlighted ? 'text-[var(--color-primary)]' : 'text-[var(--color-foreground)]'}`}>{doc.name}</h4>
                    <div className="flex items-center gap-3 mt-1 text-xs text-[var(--color-muted-foreground)]">
                      <span>{doc.size}</span>
                      <span>•</span>
                      <span>{doc.pages} pages</span>
                      <span>•</span>
                      <span>{doc.dateAdded}</span>
                    </div>
                    {isHighlighted && highlightPage && (
                      <div className="mt-2 text-sm font-medium text-[var(--color-primary)] flex items-center gap-1.5 bg-[var(--color-background)] w-fit px-2.5 py-1 rounded-md border border-[var(--color-primary)]/20 shadow-sm">
                        <FileText className="w-3.5 h-3.5" />
                        <span>Source reference linked to Page {highlightPage}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-1.5">
                    {doc.status === 'ready' ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Ready</span>
                      </>
                    ) : (
                      <>
                        <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
                        <span className="text-xs font-medium text-amber-600 dark:text-amber-400">Processing...</span>
                      </>
                    )}
                  </div>
                  <button onClick={() => handleDelete(doc.id)} className="p-2 text-[var(--color-muted-foreground)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
          {documents.length === 0 && !isUploading && (
            <div className="text-center py-10 text-[var(--color-muted-foreground)]">
              No documents uploaded yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-[var(--color-muted-foreground)]">Loading documents...</div>}>
      <DocumentsContent />
    </Suspense>
  );
}
