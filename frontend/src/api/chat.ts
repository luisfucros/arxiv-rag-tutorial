import { getAuthHeaders } from './client'
import type { ChatHistoryRequest, ChatResponse, StreamChunk } from '../types/api'

const base = () => import.meta.env.VITE_API_URL || ''

/** Extract one complete JSON object from the start of s (brace-matched, respecting strings). Returns { obj, rest } or null. */
function parseOneJson(s: string): { obj: StreamChunk; rest: string } | null {
  const start = s.indexOf('{')
  if (start === -1) return null
  let depth = 0
  let inString = false
  let escape = false
  let quote = '"'
  for (let i = start; i < s.length; i++) {
    const c = s[i]
    if (escape) {
      escape = false
      continue
    }
    if (c === '\\' && inString) {
      escape = true
      continue
    }
    if (!inString) {
      if (c === '"' || c === "'") {
        inString = true
        quote = c
        continue
      }
      if (c === '{') depth++
      else if (c === '}') {
        depth--
        if (depth === 0) {
          const slice = s.slice(start, i + 1)
          try {
            const obj = JSON.parse(slice) as StreamChunk
            return { obj, rest: s.slice(i + 1).trimStart() }
          } catch {
            return null
          }
        }
      }
    } else if (c === quote) {
      inString = false
    }
  }
  return null
}

export async function chat(
  sessionId: string,
  body: ChatHistoryRequest
): Promise<ChatResponse> {
  const res = await fetch(
    `${base()}/arxiv_assistant/chat?session_id=${encodeURIComponent(sessionId)}`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    }
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err.detail as string) || 'Chat request failed')
  }
  return res.json() as Promise<ChatResponse>
}

export async function* chatStream(
  sessionId: string,
  body: ChatHistoryRequest
): AsyncGenerator<StreamChunk> {
  const res = await fetch(
    `${base()}/arxiv_assistant/chat/stream?session_id=${encodeURIComponent(sessionId)}`,
    {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    }
  )
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err.detail as string) || 'Stream failed')
  }
  const reader = res.body?.getReader()
  if (!reader) throw new Error('No response body')
  const dec = new TextDecoder()
  let buffer = ''
  let result: { obj: StreamChunk; rest: string } | null
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += dec.decode(value, { stream: true })
      while ((result = parseOneJson(buffer)) !== null) {
        yield result.obj
        buffer = result.rest
      }
    }
    while ((result = parseOneJson(buffer)) !== null) {
      yield result.obj
      buffer = result.rest
    }
  } finally {
    reader.releaseLock()
  }
}
