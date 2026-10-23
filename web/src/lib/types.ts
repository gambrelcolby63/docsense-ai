export type Health = {
  status: string;
  provider: string;
  embedding_provider: string;
  database: string;
  model: string | null;
};

export type DocumentSummary = {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  summary: string;
  key_points: string[];
  chunk_count: number;
  provider: string;
  embedding_provider: string;
  created_at: string;
};

export type DocumentDetail = DocumentSummary & {
  extracted_text: string;
};

export type Citation = {
  label: number;
  chunk_index: number;
  text: string;
  score: number;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  message_id: number;
};

export type Message = {
  id: number;
  role: "user" | "assistant" | string;
  content: string;
  citations: Citation[];
  created_at: string;
};
