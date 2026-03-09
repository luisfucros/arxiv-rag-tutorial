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

// Chat history
export interface ChatSessionResponse {
  id: string
  owner_id: number
  title: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessageResponse {
  id: string
  session_id: string
  role: string
  content: string
  message_metadata?: Record<string, unknown> | null
  created_at: string
}

// Feedback
export type FeedbackValue = 'positive' | 'negative'

export interface FeedbackCreate {
  message_id: string
  value: FeedbackValue
  comment?: string
}

export interface FeedbackResponse {
  id: string
  user_id: number
  message_id: string
  value: FeedbackValue
  comment: string | null
  created_at: string
}

// Paper (in DB)
export interface PaperResponse {
  id: string
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  categories: string[]
  published_date: string
  pdf_url: string
  pdf_processed: boolean
  created_at: string
  updated_at: string
}

export interface PaperSearchResponse {
  papers: PaperResponse[]
  total: number
}

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
