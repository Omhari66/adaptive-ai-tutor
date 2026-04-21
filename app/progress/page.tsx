"use client";

import { useEffect, useState } from "react";
import { TrendingUp, Target, BookOpen, Loader2 } from "lucide-react";
import { getProgress } from "@/lib/api";

interface ProgressData {
  overallAccuracy: string;
  quizzesCompleted: number;
  conceptsMastered: number;
  accuracy: number[];
  weakTopics: { topic: string; score: number }[];
}

export default function ProgressPage() {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProgress()
      .then((data) => {
        setProgress(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch progress:", err);
        setError("Failed to load progress data");
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full w-full">
        <Loader2 className="w-10 h-10 animate-spin text-[var(--color-primary)]" />
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="p-8 max-w-5xl mx-auto w-full">
        <div className="text-center py-10 text-[var(--color-muted-foreground)]">
          {error || "No progress data available"}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto w-full">
      <header className="mb-10">
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Performance Analytics</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">Track your mastery across all uploaded materials</p>
      </header>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="p-6 bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400 rounded-lg">
              <TrendingUp className="w-5 h-5" />
            </div>
            <span className="font-medium text-[var(--color-muted-foreground)] text-sm">Overall Accuracy</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-[var(--color-foreground)]">{progress.overallAccuracy}</h2>
          </div>
        </div>

        <div className="p-6 bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400 rounded-lg">
              <Target className="w-5 h-5" />
            </div>
            <span className="font-medium text-[var(--color-muted-foreground)] text-sm">Quizzes Completed</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-[var(--color-foreground)]">{progress.quizzesCompleted}</h2>
          </div>
        </div>

        <div className="p-6 bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400 rounded-lg">
              <BookOpen className="w-5 h-5" />
            </div>
            <span className="font-medium text-[var(--color-muted-foreground)] text-sm">Concepts Mastered</span>
          </div>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-bold text-[var(--color-foreground)]">{progress.conceptsMastered}</h2>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trend Graph */}
        <div className="lg:col-span-2 bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-6 shadow-sm">
          <h3 className="text-base font-semibold text-[var(--color-foreground)] mb-6">Accuracy Trend</h3>
          <div className="h-64 flex items-end gap-2 md:gap-6 pt-4">
            {progress.accuracy.map((val, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2 group cursor-pointer relative">
                {/* Bar Container */}
                <div className="w-full relative bg-[var(--color-muted)] rounded-t-lg transition-all" style={{ height: '100%' }}>
                  <div
                    className="absolute bottom-0 w-full bg-[var(--color-primary)] rounded-t-md transition-all group-hover:opacity-90 group-hover:shadow-md flex justify-center"
                    style={{ height: `${val}%` }}
                  >
                    {/* Permanently visible value label above the colored bar */}
                    <span className="absolute -top-6 text-[10px] sm:text-xs font-bold text-[var(--color-foreground)]/80">
                      {val}%
                    </span>
                  </div>
                </div>
                <span className="text-xs text-[var(--color-muted-foreground)] font-medium mt-1">W{idx + 1}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Weak Topics */}
        <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-6 shadow-sm flex flex-col">
          <h3 className="text-base font-semibold text-[var(--color-foreground)] mb-6">Focus Areas</h3>
          <p className="text-sm text-[var(--color-muted-foreground)] mb-6">Topics to review based on your recent quiz scores.</p>

          <div className="space-y-5 mt-auto mb-4">
            {progress.weakTopics.length > 0 ? (
              progress.weakTopics.map((topic, idx) => (
                <div key={idx}>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-[var(--color-foreground)]">{topic.topic}</span>
                    <span className="text-xs font-semibold text-amber-500">{topic.score}%</span>
                  </div>
                  <div className="w-full h-2 bg-[var(--color-muted)] rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full" style={{ width: `${topic.score}%` }}></div>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-[var(--color-muted-foreground)]">No weak topics identified. Great job!</p>
            )}
          </div>

          <button
            onClick={() => (window.location.href = "/quiz?mode=review")}
            className="w-full mt-auto py-2.5 bg-[var(--color-primary)]/10 text-[var(--color-primary)] font-medium rounded-xl hover:bg-[var(--color-primary)]/20 transition-colors text-sm cursor-pointer"
          >
            Generate Review Quiz
          </button>
        </div>
      </div>
    </div>
  );
}
