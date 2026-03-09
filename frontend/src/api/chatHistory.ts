import { apiRequest } from './client'
import type { ChatMessageResponse, ChatSessionResponse } from '../types/api'

export function listSessions(
  limit = 20,
  offset = 0
): Promise<ChatSessionResponse[]> {
  return apiRequest<ChatSessionResponse[]>(
    `/chat_history/sessions?limit=${limit}&offset=${offset}`
  )
}

export function listMessages(
  sessionId: string,
  limit = 100,
  offset = 0
): Promise<ChatMessageResponse[]> {
  return apiRequest<ChatMessageResponse[]>(
    `/chat_history/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`
  )
}
