// Auth
export interface Token {
  access_token: string
  token_type: string
}

export interface UserOut {
  id: number
  email: string
  full_name: string | null
  role: string
  created_at: string
}

export interface UserCreate {
  email: string
  password: string
  full_name?: string
  role?: string
}

// Chat
export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  role: ChatRole
  content: string
}

export interface ChatHistoryRequest {
  chat_history: ChatMessage[]
}

export interface ChatResponse {
  answer: string
  message_id: string
}

// Stream chunk (NDJSON from backend)
export type StreamChunk =
  | { type: 'content'; text: string }
  | { type: 'message_id'; message_id: string }

// Tasks & ingestion
export interface TaskResponse {
  task_id: string
  status: string
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  db_status?: string
  result?: Record<string, unknown> | null
}

export interface PaperMetadataRequest {
  paper_ids: string[]
  process_pdfs: boolean
  store_to_db: boolean
}

// Arxiv (optional for search)
export interface ArxivPaper {
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  categories: string[]
  published_date: string
  pdf_url?: string
}

export interface PaperRequest {
  query: string
}
