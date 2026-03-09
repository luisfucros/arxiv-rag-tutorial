import { apiRequest } from './client'
import type { FeedbackCreate, FeedbackResponse } from '../types/api'

export function createFeedback(body: FeedbackCreate): Promise<FeedbackResponse> {
  return apiRequest<FeedbackResponse>('/feedback', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function getFeedbackByMessage(
  messageId: string
): Promise<FeedbackResponse | null> {
  try {
    return await apiRequest<FeedbackResponse>(`/feedback/message/${messageId}`)
  } catch {
    return null
  }
}

export function updateFeedback(
  feedbackId: string,
  body: { value?: import('../types/api').FeedbackValue; comment?: string }
): Promise<FeedbackResponse> {
  return apiRequest<FeedbackResponse>(`/feedback/${feedbackId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}
