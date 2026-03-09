import { apiRequest, getAuthHeaders } from './client'
import type { TaskResponse, TaskStatusResponse } from '../types/api'

export function listTasks(): Promise<TaskStatusResponse[]> {
  return apiRequest<TaskStatusResponse[]>('/tasks/')
}

export function getTask(taskId: string): Promise<TaskStatusResponse> {
  return apiRequest<TaskStatusResponse>(`/tasks/${taskId}`)
}

export function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return apiRequest<TaskStatusResponse>(`/tasks/status/${taskId}`)
}

export function retryTask(taskId: string): Promise<TaskResponse> {
  return apiRequest<TaskResponse>(`/tasks/retry/${taskId}`, {
    method: 'POST',
  })
}

const base = () => import.meta.env.VITE_API_URL || ''

/** Subscribe to task status SSE. Returns unsubscribe. */
export function openTaskStream(
  taskId: string,
  onMessage: (data: TaskStatusResponse & { error?: string }) => void,
  onError?: (err: string) => void,
  onClose?: () => void
): () => void {
  const url = `${base()}/tasks/stream/${taskId}?poll_interval=1`
  let aborted = false
  const ac = new AbortController()
  fetch(url, {
    headers: getAuthHeaders(),
    signal: ac.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        onError?.(`${res.status}: ${res.statusText}`)
        onClose?.()
        return
      }
      const reader = res.body?.getReader()
      if (!reader) {
        onClose?.()
        return
      }
      const dec = new TextDecoder()
      let buffer = ''
      try {
        while (!aborted) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += dec.decode(value, { stream: true })
          const events = buffer.split('\n\n')
          buffer = events.pop() ?? ''
          for (const block of events) {
            let dataLine: string | null = null
            for (const line of block.split('\n')) {
              if (line.startsWith('data: ')) dataLine = line.slice(6)
            }
            if (!dataLine) continue
            try {
              const data = JSON.parse(dataLine) as TaskStatusResponse & { error?: string; message?: string }
              if (data.error) onError?.(data.error)
              else onMessage(data)
            } catch {
              // skip
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
      onClose?.()
    })
    .catch((err) => {
      if (!aborted) onError?.(err instanceof Error ? err.message : String(err))
      onClose?.()
    })
  return () => {
    aborted = true
    ac.abort()
  }
}
