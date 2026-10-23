"use client";

import { useEffect, useState } from "react";

import { getHealth, listDocuments } from "@/lib/api";
import type { DocumentSummary, Health } from "@/lib/types";

import { DocumentList } from "./DocumentList";
import { UploadPanel } from "./UploadPanel";

export function HomeScreen() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [rows, status] = await Promise.all([listDocuments(), getHealth()]);
        if (!cancelled) {
          setDocuments(rows);
          setHealth(status);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "Could not reach the API.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-4 pb-20 pt-8 sm:pt-12">
      <p className="text-sm font-semibold text-teal">For the long PDF you meant to read</p>
      <h1 className="mt-2 max-w-xl font-serif text-4xl leading-[1.1] tracking-tight sm:text-5xl">
        Ask a document anything.
      </h1>
      <p className="mt-4 max-w-xl text-base leading-relaxed text-muted sm:text-lg">
        Upload a PDF or a photo of a page. DocSense pulls out the text, writes a short summary,
        and answers questions with the passage it used.
      </p>

      <UploadPanel />

      <section className="mt-10" aria-labelledby="history-heading">
        <div className="mb-3 flex items-end justify-between gap-3">
          <h2 id="history-heading" className="font-serif text-2xl tracking-tight">
            Recent documents
          </h2>
          {health ? <ProviderNote health={health} /> : null}
        </div>
        {loading ? <p className="text-sm text-muted">Loading history…</p> : null}
        {loadError ? (
          <p role="alert" className="rounded-2xl border border-clay/30 bg-white px-4 py-3 text-sm text-clay">
            {loadError}
          </p>
        ) : null}
        {!loading && !loadError ? <DocumentList documents={documents} /> : null}
      </section>
    </main>
  );
}

function ProviderNote({ health }: { health: Health }) {
  const live = health.provider !== "mock";
  const label = live ? `Live model${health.model ? ` · ${health.model}` : ""}` : "Mock provider";
  return (
    <p className="max-w-[14rem] text-right text-xs leading-snug text-muted">
      <span className="font-semibold text-ink">{label}</span>
      {live
        ? " Answers cite retrieved passages."
        : " Answers quote the file. No model API is called."}
    </p>
  );
}
