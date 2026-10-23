import type { ChatResponse, DocumentDetail, DocumentSummary, Health, Message } from "./types";

export function apiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return configured.replace(/\/$/, "");
}

export async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    if (typeof data.detail === "string" && data.detail.trim()) return data.detail;
    if (Array.isArray(data.detail)) {
      const messages = data.detail
        .map((item) => {
          if (typeof item === "string") return item;
          if (item && typeof item === "object" && "msg" in item) {
            const msg = (item as { msg?: unknown }).msg;
            return typeof msg === "string" ? msg : "";
          }
          return "";
        })
        .filter(Boolean);
      if (messages.length > 0) return messages.join(" ");
    }
  } catch {
    // Body was empty or not JSON.
  }
  return `Request failed (${response.status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBase()}${path}`, init);
  } catch {
    throw new Error(
      `The API at ${apiBase()} is not reachable. Start it with docker compose, or run uvicorn on port 8000.`,
    );
  }
  if (!response.ok) throw new Error(await readError(response));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function getHealth(): Promise<Health> {
  return request<Health>("/api/health");
}

export function listDocuments(): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>("/api/documents");
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return request<DocumentDetail>(`/api/documents/${id}`);
}

export function getMessages(id: string): Promise<Message[]> {
  return request<Message[]>(`/api/documents/${id}/messages`);
}

export function uploadDocument(file: File): Promise<DocumentDetail> {
  const body = new FormData();
  body.append("file", file);
  return request<DocumentDetail>("/api/documents", { method: "POST", body });
}

export function askDocument(id: string, question: string): Promise<ChatResponse> {
  return request<ChatResponse>(`/api/documents/${id}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function deleteDocument(id: string): Promise<void> {
  return request<void>(`/api/documents/${id}`, { method: "DELETE" });
}
