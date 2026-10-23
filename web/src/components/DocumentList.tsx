import Link from "next/link";

import { formatBytes, formatWhen } from "@/lib/format";
import type { DocumentSummary } from "@/lib/types";

export function DocumentList({ documents }: { documents: DocumentSummary[] }) {
  if (documents.length === 0) {
    return (
      <p className="rounded-3xl border border-dashed border-line bg-card/70 px-4 py-8 text-sm leading-relaxed text-muted">
        Nothing here yet. Upload a file, or try the sample brief, and it will stay in this list.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {documents.map((document) => (
        <li key={document.id}>
          <Link
            href={`/documents/${document.id}`}
            className="block rounded-3xl border border-line bg-card px-4 py-4 shadow-card transition hover:border-teal/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-semibold leading-snug">{document.filename}</h3>
              <time className="shrink-0 text-xs text-muted" dateTime={document.created_at}>
                {formatWhen(document.created_at)}
              </time>
            </div>
            <p className="mt-2 line-clamp-3 text-sm leading-relaxed text-ink/80">{document.summary}</p>
            <p className="mt-3 text-xs uppercase tracking-wide text-muted">
              {formatBytes(document.file_size)} · {document.chunk_count}{" "}
              {document.chunk_count === 1 ? "passage" : "passages"} · {document.provider}
            </p>
          </Link>
        </li>
      ))}
    </ul>
  );
}
