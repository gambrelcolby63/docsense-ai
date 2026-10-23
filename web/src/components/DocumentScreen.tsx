"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { askDocument, deleteDocument, getDocument, getMessages } from "@/lib/api";
import { citationLabel, formatBytes, formatScore, formatWhen, questionFromPoint, splitCitations } from "@/lib/format";
import type { Citation, DocumentDetail, Message } from "@/lib/types";

export function DocumentScreen({ id }: { id: string }) {
  const router = useRouter();
  const endRef = useRef<HTMLDivElement>(null);
  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    (async () => {
      try {
        const [detail, history] = await Promise.all([getDocument(id), getMessages(id)]);
        if (!cancelled) {
          setDocument(detail);
          setMessages(history);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not load this document.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!document) return;
    const previous = window.document.title;
    window.document.title = `${document.filename} · DocSense`;
    return () => {
      window.document.title = previous;
    };
  }, [document]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  async function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setChatError(null);
    setSending(true);
    setQuestion("");
    try {
      const result = await askDocument(id, trimmed);
      const now = new Date().toISOString();
      setMessages((current) => [
        ...current,
        {
          id: -result.message_id,
          role: "user",
          content: trimmed,
          citations: [],
          created_at: now,
        },
        {
          id: result.message_id,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
          created_at: now,
        },
      ]);
    } catch (err) {
      setQuestion(trimmed);
      setChatError(err instanceof Error ? err.message : "The question did not go through.");
    } finally {
      setSending(false);
    }
  }

  async function remove() {
    setDeleting(true);
    try {
      await deleteDocument(id);
      router.push("/");
    } catch (err) {
      setDeleting(false);
      setChatError(err instanceof Error ? err.message : "Could not delete this document.");
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <p className="text-sm text-muted">Opening the document…</p>
      </main>
    );
  }

  if (error || !document) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <p role="alert" className="text-sm text-clay">
          {error || "Document not found."}
        </p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-teal">
          Back to documents
        </Link>
      </main>
    );
  }

  const suggestions = document.key_points.slice(0, 3).map(questionFromPoint);

  return (
    <main className="mx-auto max-w-3xl px-4 pb-8 pt-6">
      <Link href="/" className="text-sm font-semibold text-teal">
        ← All documents
      </Link>
      <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl leading-tight tracking-tight sm:text-4xl">{document.filename}</h1>
          <p className="mt-2 text-sm text-muted">
            {formatWhen(document.created_at)} · {formatBytes(document.file_size)} · {document.chunk_count}{" "}
            {document.chunk_count === 1 ? "passage" : "passages"} ·{" "}
            {document.provider === "mock" ? "Mock provider" : document.provider}
          </p>
        </div>
        {confirmingDelete ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="min-h-11 rounded-full px-3 text-sm font-semibold text-muted"
              onClick={() => setConfirmingDelete(false)}
              disabled={deleting}
            >
              Cancel
            </button>
            <button
              type="button"
              className="min-h-11 rounded-full bg-clay px-4 text-sm font-semibold text-white disabled:opacity-60"
              onClick={() => void remove()}
              disabled={deleting}
            >
              {deleting ? "Deleting…" : "Delete"}
            </button>
          </div>
        ) : (
          <button
            type="button"
            className="min-h-11 rounded-full border border-line bg-card px-4 text-sm font-semibold"
            onClick={() => setConfirmingDelete(true)}
          >
            Delete
          </button>
        )}
      </div>

      <section className="mt-6 rounded-3xl border border-line bg-card p-5 shadow-card" aria-labelledby="summary-heading">
        <h2 id="summary-heading" className="text-xs font-semibold uppercase tracking-[0.16em] text-teal">
          Summary
        </h2>
        <p className="mt-3 text-base leading-relaxed">{document.summary}</p>
      </section>

      <section className="mt-4 rounded-3xl border border-line bg-card p-5 shadow-card" aria-labelledby="points-heading">
        <h2 id="points-heading" className="text-xs font-semibold uppercase tracking-[0.16em] text-teal">
          Key points
        </h2>
        <ol className="mt-3 space-y-3">
          {document.key_points.map((point, index) => (
            <li key={`${index}-${point.slice(0, 24)}`} className="flex gap-3 text-sm leading-relaxed">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-teal-soft text-xs font-semibold text-teal-dark">
                {index + 1}
              </span>
              <span>{point}</span>
            </li>
          ))}
        </ol>
      </section>

      <details className="mt-4 rounded-3xl border border-line bg-card">
        <summary className="cursor-pointer px-5 py-4 text-sm font-semibold">
          Extracted text
          <span className="ml-2 font-normal text-muted">
            {document.extracted_text.length.toLocaleString()} characters
          </span>
        </summary>
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap px-5 pb-5 text-sm leading-relaxed text-ink/90">
          {document.extracted_text}
        </pre>
      </details>

      <section className="mt-8" aria-labelledby="chat-heading">
        <h2 id="chat-heading" className="font-serif text-2xl tracking-tight">
          Ask a question
        </h2>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          Answers stay inside this document and show the passage they came from.
        </p>

        {messages.length === 0 ? (
          <div className="mt-4 flex flex-col gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                className="rounded-2xl border border-line bg-card px-4 py-3 text-left text-sm leading-relaxed hover:border-teal/40 disabled:opacity-60"
                onClick={() => void submit(suggestion)}
                disabled={sending}
              >
                {suggestion}
              </button>
            ))}
          </div>
        ) : null}

        <div className="mt-4 space-y-4" aria-live="polite">
          {messages.map((message) => (
            <MessageBubble key={`${message.role}-${message.id}`} message={message} />
          ))}
          {sending ? <p className="text-sm text-muted">Looking through the passages…</p> : null}
          <div ref={endRef} />
        </div>
      </section>

      <form
        className="sticky bottom-0 -mx-4 mt-4 border-t border-line/80 bg-paper/95 px-4 py-3 backdrop-blur"
        style={{ paddingBottom: "calc(0.75rem + env(safe-area-inset-bottom))" }}
        onSubmit={(event) => {
          event.preventDefault();
          void submit(question);
        }}
      >
        {chatError ? (
          <p role="alert" className="mb-2 text-sm text-clay">
            {chatError}
          </p>
        ) : null}
        <div className="flex items-end gap-2">
          <label className="sr-only" htmlFor="question">
            Question
          </label>
          <textarea
            id="question"
            rows={2}
            value={question}
            placeholder="Ask something this document can answer"
            className="min-h-12 flex-1 resize-none rounded-2xl border border-line bg-card px-3 py-3 text-base leading-snug focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/30"
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit(question);
              }
            }}
          />
          <button
            type="submit"
            className="inline-flex min-h-12 items-center justify-center rounded-full bg-teal px-4 text-sm font-semibold text-white hover:bg-teal-dark disabled:opacity-60"
            disabled={sending || question.trim().length === 0}
          >
            Send
          </button>
        </div>
      </form>
    </main>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const mine = message.role === "user";
  return (
    <article className={mine ? "flex justify-end" : ""}>
      <div
        className={
          mine
            ? "max-w-[90%] rounded-3xl rounded-br-md bg-teal px-4 py-3 text-sm leading-relaxed text-white"
            : "max-w-full rounded-3xl border border-line bg-card px-4 py-3 text-sm leading-relaxed shadow-card"
        }
      >
        <p className="whitespace-pre-wrap">
          {mine ? (
            message.content
          ) : (
            splitCitations(message.content).map((part, index) =>
              part.kind === "cite" ? (
                <sup key={index} className="ml-0.5 text-[11px] font-semibold text-clay">
                  {part.value}
                </sup>
              ) : (
                <span key={index}>{part.value}</span>
              ),
            )
          )}
        </p>
        {message.citations.length > 0 ? <CitationList citations={message.citations} /> : null}
      </div>
    </article>
  );
}

function CitationList({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-3 space-y-3 border-t border-line pt-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-clay">From the document</p>
      {citations.map((citation) => (
        <blockquote key={citation.label} className="border-l-2 border-clay/70 pl-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
            {citationLabel(citation.label)} · {formatScore(citation.score)}
          </p>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-ink/90">{citation.text}</p>
        </blockquote>
      ))}
    </div>
  );
}
