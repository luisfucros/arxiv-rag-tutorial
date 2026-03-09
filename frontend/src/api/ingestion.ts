import { apiRequest } from './client'
import type { PaperMetadataRequest, TaskResponse } from '../types/api'

export function fetchMetadata(payload: PaperMetadataRequest): Promise<TaskResponse> {
  return apiRequest<TaskResponse>('/metadata/fetch', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
