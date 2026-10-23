"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { uploadDocument } from "@/lib/api";
import { isProbablyDocument, MAX_UPLOAD_BYTES } from "@/lib/format";

export function UploadPanel() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function send(file: File) {
    setError(null);
    if (!isProbablyDocument(file)) {
      setError("Upload a PDF or an image (PNG, JPEG, WEBP, or GIF).");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError("That file is larger than 15 MB.");
      return;
    }
    setBusy(true);
    setStatus(`Reading ${file.name}…`);
    try {
      const document = await uploadDocument(file);
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setBusy(false);
      setStatus(null);
    }
  }

  async function useSample() {
    setError(null);
    setBusy(true);
    setStatus("Loading the sample brief…");
    try {
      const response = await fetch("/sample-brief.pdf");
      if (!response.ok) throw new Error("The sample brief is missing from this build.");
      const blob = await response.blob();
      const file = new File([blob], "sample-brief.pdf", { type: "application/pdf" });
      await send(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the sample.");
      setBusy(false);
      setStatus(null);
    }
  }

  return (
    <section className="mt-8" aria-labelledby="upload-heading">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          const file = event.dataTransfer.files?.[0];
          if (file) void send(file);
        }}
        className={`rounded-3xl border bg-card px-4 py-6 shadow-card sm:px-6 ${
          dragging ? "border-teal ring-2 ring-teal/30" : "border-line"
        }`}
      >
        <h2 id="upload-heading" className="font-serif text-2xl tracking-tight">
          Drop a file here
        </h2>
        <p className="mt-1 text-sm leading-relaxed text-muted">
          PDF or a photo of a page, up to 15 MB. For a photo, fill the frame and keep the page flat.
        </p>
        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <button
            type="button"
            className="inline-flex min-h-12 items-center justify-center rounded-full bg-teal px-5 text-sm font-semibold text-white hover:bg-teal-dark disabled:opacity-60"
            onClick={() => fileRef.current?.click()}
            disabled={busy}
          >
            Choose file
          </button>
          <button
            type="button"
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-line bg-white px-5 text-sm font-semibold hover:border-teal/40 disabled:opacity-60"
            onClick={() => cameraRef.current?.click()}
            disabled={busy}
          >
            Use camera
          </button>
          <button
            type="button"
            className="inline-flex min-h-12 items-center justify-center rounded-full border border-line bg-white px-5 text-sm font-semibold hover:border-teal/40 disabled:opacity-60"
            onClick={() => void useSample()}
            disabled={busy}
          >
            Try the sample
          </button>
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="application/pdf,image/png,image/jpeg,image/webp,image/gif"
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void send(file);
            event.target.value = "";
          }}
        />
        <input
          ref={cameraRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="sr-only"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void send(file);
            event.target.value = "";
          }}
        />
        {status ? <p className="mt-4 text-sm text-teal">{status}</p> : null}
        {error ? (
          <p role="alert" className="mt-4 text-sm text-clay">
            {error}
          </p>
        ) : null}
      </div>
    </section>
  );
}
