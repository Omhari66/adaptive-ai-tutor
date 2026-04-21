"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, ArrowRight, BrainCircuit, Loader2 } from "lucide-react";
import { generateQuiz, QuizQuestion } from "@/lib/api";

export default function QuizPage() {
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [quizTitle, setQuizTitle] = useState("Active Recall Review");
  const [quizId, setQuizId] = useState<string | null>(null);
  const [userAnswers, setUserAnswers] = useState<number[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [score, setScore] = useState<{correctCount: number, totalQuestions: number, accuracy: number} | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const startNewQuiz = async () => {
    setIsGenerating(true);
    setQuestions([]);
    setCurrentIdx(0);
    setSelectedIdx(null);
    setIsAnswered(false);
    setUserAnswers([]);
    setScore(null);
    setQuizId(null);
    
    try {
      const data = await generateQuiz([], 5); // Hits all documents if empty array
      setQuizTitle(data.title);
      setQuestions(data.questions);
      setQuizId(data.quizId);
    } catch (error: any) {
      // Use console.log instead of error to prevent Next.js from throwing scary terminal logs for expected validation errors
      console.log("Quiz generation notice:", error);
      alert(error.message || "Error generating quiz. Please make sure you have uploaded and processed at least one document first!");
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    // Generate an initial quiz if empty
    if (questions.length === 0 && !isGenerating) {
      startNewQuiz();
    }
  }, []);

  const handleSelect = (idx: number) => {
    if (isAnswered) return;
    setSelectedIdx(idx);
    setIsAnswered(true);
    setUserAnswers(prev => [...prev, idx]);
  };

  const nextQuestion = async () => {
    if (currentIdx < questions.length - 1) {
      setCurrentIdx(currentIdx + 1);
      setSelectedIdx(null);
      setIsAnswered(false);
    } else {
      // Completed, submit and show score
      if (quizId && userAnswers.length === questions.length) {
        setIsSubmitting(true);
        try {
          // Dynamic import or assumed global API if added
          const { submitQuiz } = await import("@/lib/api");
          const result = await submitQuiz(quizId, userAnswers);
          setScore(result);
        } catch (error) {
          console.error("Submit failed", error);
        } finally {
          setIsSubmitting(false);
        }
      }
    }
  };

  if (isGenerating) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full">
        <Loader2 className="w-10 h-10 animate-spin text-[var(--color-primary)] mb-4" />
        <h2 className="text-xl font-medium">Synthesizing material...</h2>
        <p className="text-[var(--color-muted-foreground)]">Groq is generating your personalized quiz.</p>
      </div>
    );
  }

  if (isSubmitting) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full">
        <Loader2 className="w-10 h-10 animate-spin text-[var(--color-primary)] mb-4" />
        <h2 className="text-xl font-medium">Grading quiz...</h2>
        <p className="text-[var(--color-muted-foreground)]">Saving results to your profile.</p>
      </div>
    );
  }

  if (score) {
    return (
      <div className="flex flex-col items-center justify-center h-full w-full max-w-lg mx-auto text-center p-8">
        <div className="w-24 h-24 rounded-full bg-[var(--color-primary)]/10 flex items-center justify-center mb-6">
          <BrainCircuit className="w-12 h-12 text-[var(--color-primary)]" />
        </div>
        <h2 className="text-3xl font-bold mb-2">Quiz Complete!</h2>
        <p className="text-xl text-[var(--color-muted-foreground)] mb-8">
          You scored {score.correctCount} out of {score.totalQuestions} ({Math.round(score.accuracy)}%)
        </p>
        <button 
          onClick={startNewQuiz}
          className="px-8 py-4 bg-[var(--color-primary)] text-white font-medium rounded-xl hover:bg-[var(--color-primary)]/90 transition-colors shadow-sm w-full"
        >
          Generate New Quiz
        </button>
      </div>
    );
  }

  if (questions.length === 0) return null;

  const currentQ = questions[currentIdx];

  return (
    <div className="p-8 max-w-4xl mx-auto w-full h-full flex flex-col justify-center">
      <div className="mb-8 text-center">
        <div className="inline-flex items-center justify-center p-3 bg-[var(--color-primary)]/10 text-[var(--color-primary)] rounded-2xl mb-4">
          <BrainCircuit className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-bold text-[var(--color-foreground)] tracking-tight">{quizTitle}</h1>
        <p className="text-[var(--color-muted-foreground)] mt-2">Question {currentIdx + 1} of {questions.length}</p>
      </div>

      <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-3xl p-8 md:p-10 shadow-sm max-w-3xl mx-auto w-full">
        <h2 className="text-xl md:text-2xl font-medium text-[var(--color-foreground)] mb-8 leading-relaxed">
          {currentQ.question}
        </h2>

        <div className="space-y-3">
          {currentQ.options.map((option, idx) => {
            const isSelected = selectedIdx === idx;
            const isCorrect = currentQ.correctAnswer === idx;
            
            let btnStyle = "bg-[var(--color-background)] border-[var(--color-border)] hover:border-[var(--color-primary)] hover:bg-[var(--color-muted)]";
            
            if (isAnswered) {
              if (isCorrect) {
                 btnStyle = "bg-emerald-50 border-emerald-500 text-emerald-800 dark:bg-emerald-500/10 dark:border-emerald-500 dark:text-emerald-300";
              } else if (isSelected && !isCorrect) {
                 btnStyle = "bg-red-50 border-red-500 text-red-800 dark:bg-red-500/10 dark:border-red-500 dark:text-red-300";
              } else {
                 btnStyle = "bg-[var(--color-background)] border-[var(--color-border)] opacity-50";
              }
            }

            return (
              <button
                key={idx}
                onClick={() => handleSelect(idx)}
                disabled={isAnswered}
                className={`w-full text-left px-6 py-4 rounded-xl border-2 transition-all ${btnStyle} group flex justify-between items-center`}
              >
                <span className="font-medium">{option}</span>
                {isAnswered && isCorrect && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                {isAnswered && isSelected && !isCorrect && <XCircle className="w-5 h-5 text-red-500" />}
              </button>
            )
          })}
        </div>

        {isAnswered && (
          <div className="mt-8 pt-6 border-t border-[var(--color-border)] flex items-center justify-between animate-in fade-in slide-in-from-bottom-2">
            <div className="max-w-md">
              {currentQ.explanation && (
                <p className="text-sm text-[var(--color-muted-foreground)] mb-1">
                  <strong className="text-[var(--color-foreground)]">Explanation: </strong>
                  {currentQ.explanation}
                </p>
              )}
            </div>
            <button 
              onClick={nextQuestion}
              className="flex items-center gap-2 px-6 py-3 bg-[var(--color-primary)] text-white font-medium rounded-xl hover:bg-[var(--color-primary)]/90 transition-colors shadow-sm shrink-0 ml-4"
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
