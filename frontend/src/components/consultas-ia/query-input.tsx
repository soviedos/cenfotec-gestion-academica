"use client";

import { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";

interface QueryInputProps {
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

export function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [question, setQuestion] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isLoading) return;
    onSubmit(trimmed);
    setQuestion("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3">
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Escribe tu pregunta sobre las evaluaciones docentes..."
        rows={2}
        disabled={isLoading}
        className="flex-1 resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
        aria-label="Pregunta"
      />
      <Button
        type="submit"
        disabled={isLoading || !question.trim()}
        className="self-end"
        aria-label="Enviar consulta"
      >
        <Send className="mr-2 h-4 w-4" />
        Consultar
      </Button>
    </form>
  );
}
