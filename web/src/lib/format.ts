const EXTENSIONS = [".pdf", ".png", ".jpg", ".jpeg", ".webp", ".gif"];

export function formatBytes(size: number): string {
  if (!Number.isFinite(size) || size < 0) return "0 B";
  if (size < 1024) return `${Math.round(size)} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatWhen(iso: string, timeZone?: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    ...(timeZone ? { timeZone } : {}),
  }).format(date);
}

export function formatScore(score: number): string {
  if (!Number.isFinite(score)) return "0% match";
  const percent = Math.max(0, Math.min(100, Math.round(score * 100)));
  return `${percent}% match`;
}

export function citationLabel(label: number): string {
  return `Passage ${label}`;
}

export function questionFromPoint(point: string): string {
  const trimmed = point.replace(/\s+/g, " ").trim().replace(/[.?!]+$/, "");
  const words = trimmed.split(" ").filter(Boolean).slice(0, 12).join(" ");
  return `What does the document say about ${words}?`;
}

export type AnswerPart = { kind: "text" | "cite"; value: string };

export function splitCitations(answer: string): AnswerPart[] {
  return answer
    .split(/(\[\d+\])/g)
    .filter((part) => part.length > 0)
    .map((part) => ({
      kind: /^\[\d+\]$/.test(part) ? "cite" : "text",
      value: part,
    }));
}

export function isProbablyDocument(file: { name: string; type: string }): boolean {
  const name = file.name.toLowerCase();
  if (EXTENSIONS.some((extension) => name.endsWith(extension))) return true;
  return file.type === "application/pdf" || file.type.startsWith("image/");
}

export const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;
