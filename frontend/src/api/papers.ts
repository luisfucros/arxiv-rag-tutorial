import { apiRequest } from './client'
import type { PaperSearchResponse } from '../types/api'

export function listPapers(
  limit = 20,
  offset = 0
): Promise<PaperSearchResponse> {
  return apiRequest<PaperSearchResponse>(
    `/paper/?limit=${limit}&offset=${offset}`
  )
}
