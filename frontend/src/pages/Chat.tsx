import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { chatStream } from '../api/chat'
import { listMessages, listSessions } from '../api/chatHistory'
import { createFeedback, getFeedbackByMessage, updateFeedback } from '../api/feedback'
import type { ChatMessage as ChatMessageType } from '../types/api'
import type { ChatMessageResponse, ChatSessionResponse } from '../types/api'
import type { FeedbackValue } from '../types/api'
import styles from './Chat.module.css'

function randomSessionId(): string {
  return crypto.randomUUID()
}

export interface DisplayMessage extends ChatMessageType {
  id?: string
}

function toDisplayMessage(m: ChatMessageResponse): DisplayMessage {
  return { role: m.role as 'user' | 'assistant', content: m.content, id: m.id }
}

export function Chat() {
  const queryClient = useQueryClient()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [negativeFeedbackMessageId, setNegativeFeedbackMessageId] = useState<string | null>(null)
  const [feedbackComment, setFeedbackComment] = useState('')
  const [messageFeedback, setMessageFeedback] = useState<
    Record<string, { id: string; value: FeedbackValue }>
  >({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: sessions = [] } = useQuery({
    queryKey: ['chat-sessions'],
    queryFn: () => listSessions(50, 0),
  })

  const currentSessionId = sessionId ?? (sessions[0]?.id ? String(sessions[0].id) : null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const loadSession = useCallback(async (sid: string) => {
    setSessionId(sid)
    setNegativeFeedbackMessageId(null)
    setMessageFeedback({})
    try {
      const msgs = await listMessages(sid)
      setMessages(msgs.map(toDisplayMessage))
      setError(null)
      const assistantMessages = msgs.filter((m) => m.role === 'assistant' && m.id)
      const feedbackEntries = await Promise.all(
        assistantMessages.map(async (m) => {
          const fb = await getFeedbackByMessage(m.id!)
          return fb ? { messageId: m.id!, id: fb.id, value: fb.value as FeedbackValue } : null
        })
      )
      const next: Record<string, { id: string; value: FeedbackValue }> = {}
      feedbackEntries.forEach((e) => {
        if (e) next[e.messageId] = { id: e.id, value: e.value }
      })
      setMessageFeedback(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session')
      setMessages([])
    }
  }, [])

  const handleNewChat = useCallback(() => {
    const sid = randomSessionId()
    setSessionId(sid)
    setMessages([])
    setError(null)
    queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
  }, [queryClient])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    const sid = currentSessionId ?? randomSessionId()
    if (!currentSessionId) setSessionId(sid)

    setInput('')
    setError(null)
    const userMessage: DisplayMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    const history: ChatMessageType[] = [
      ...messages.filter((m) => m.role && m.content).map(({ role, content }) => ({ role, content })),
      userMessage,
    ]
    const assistantPlaceholder: DisplayMessage = { role: 'assistant', content: '' }
    setMessages((prev) => [...prev, assistantPlaceholder])

    let accumulated = ''
    let lastMessageId: string | undefined
    try {
      for await (const chunk of chatStream(sid, { chat_history: history })) {
        if (chunk.type === 'content') {
          accumulated += chunk.text
          setMessages((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            if (last?.role === 'assistant') {
              next[next.length - 1] = { ...last, content: accumulated }
            }
            return next
          })
        } else if (chunk.type === 'message_id') {
          lastMessageId = chunk.message_id
        }
      }
      if (lastMessageId) {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant') {
            next[next.length - 1] = { ...last, id: lastMessageId }
          }
          return next
        })
      }
      if (!accumulated) {
        setMessages((prev) => {
          const next = [...prev]
          const last = next[next.length - 1]
          if (last?.role === 'assistant' && !last.content) {
            next[next.length - 1] = { ...last, content: 'No response.' }
          }
          return next
        })
      }
      queryClient.invalidateQueries({ queryKey: ['chat-sessions'] })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setMessages((prev) => prev.filter((m) => m.content !== ''))
    } finally {
      setLoading(false)
    }
  }, [input, loading, messages, currentSessionId, queryClient])

  const handleFeedback = useCallback(
    async (messageId: string, value: FeedbackValue) => {
      const existing = messageFeedback[messageId]
      try {
        if (existing) {
          const updated = await updateFeedback(existing.id, { value })
          setMessageFeedback((prev) => ({
            ...prev,
            [messageId]: { id: updated.id, value: updated.value },
          }))
          if (value === 'positive') {
            setNegativeFeedbackMessageId(null)
            setFeedbackComment('')
          }
        } else {
          const created = await createFeedback({ message_id: messageId, value })
          setMessageFeedback((prev) => ({
            ...prev,
            [messageId]: { id: created.id, value: created.value },
          }))
        }
      } catch {
        // ignore
      }
    },
    [messageFeedback]
  )

  const handleNegativeClick = useCallback((messageId: string) => {
    const existing = messageFeedback[messageId]
    if (existing?.value === 'negative') {
      setNegativeFeedbackMessageId((prev) => (prev === messageId ? null : messageId))
    } else if (!existing) {
      setNegativeFeedbackMessageId((prev) => (prev === messageId ? null : messageId))
      setFeedbackComment('')
    } else {
      handleFeedback(messageId, 'negative')
    }
  }, [messageFeedback, handleFeedback])

  const submitNegativeFeedback = useCallback(
    async (messageId: string) => {
      const existing = messageFeedback[messageId]
      try {
        const comment = feedbackComment.trim() || undefined
        if (existing) {
          const updated = await updateFeedback(existing.id, {
            value: 'negative',
            comment: comment || undefined,
          })
          setMessageFeedback((prev) => ({
            ...prev,
            [messageId]: { id: updated.id, value: updated.value },
          }))
        } else {
          const created = await createFeedback({
            message_id: messageId,
            value: 'negative',
            comment,
          })
          setMessageFeedback((prev) => ({
            ...prev,
            [messageId]: { id: created.id, value: created.value },
          }))
        }
        setNegativeFeedbackMessageId(null)
        setFeedbackComment('')
      } catch {
        // ignore
      }
    },
    [feedbackComment, messageFeedback]
  )

  const selectSession = useCallback(
    (s: ChatSessionResponse) => {
      const sid = String(s.id)
      if (sid === currentSessionId) return
      loadSession(sid)
    },
    [currentSessionId, loadSession]
  )

  useEffect(() => {
    if (sessionId === null && sessions.length > 0 && messages.length === 0) {
      loadSession(String(sessions[0].id))
    }
  }, [sessionId, sessions, messages.length, loadSession])

  return (
    <div className={styles.chat}>
      <aside className={styles.sidebar}>
        <button type="button" className={styles.newChat} onClick={handleNewChat}>
          + New chat
        </button>
        <ul className={styles.sessionList}>
          {sessions.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                className={currentSessionId === String(s.id) ? styles.sessionActive : styles.session}
                onClick={() => selectSession(s)}
              >
                {s.title || `Chat ${String(s.id).slice(0, 8)}`}
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <div className={styles.main}>
        <div className={styles.header}>
          <h1>arXiv Assistant</h1>
          <p className={styles.subtitle}>
            {currentSessionId ? (
              <>Session: <code>{currentSessionId.slice(0, 8)}…</code></>
            ) : (
              'Start a new chat or select one from the sidebar.'
            )}
          </p>
        </div>

        <div className={styles.messages}>
          {messages.length === 0 && (
            <div className={styles.empty}>
              <p>Send a message to start. I can search and reason over arXiv papers.</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={msg.id ?? i}
              className={msg.role === 'user' ? styles.msgUser : styles.msgAssistant}
            >
              <span className={styles.role}>{msg.role === 'user' ? 'You' : 'Assistant'}</span>
              <div className={styles.content}>
                {msg.content || (loading && i === messages.length - 1 ? '…' : '')}
              </div>
              {msg.role === 'assistant' && msg.id && (
                <>
                  <div className={styles.feedback}>
                    <button
                      type="button"
                      aria-label="Positive feedback"
                      className={
                        messageFeedback[msg.id]?.value === 'positive'
                          ? styles.feedbackSentPositive
                          : ''
                      }
                      onClick={() => handleFeedback(msg.id!, 'positive')}
                    >
                      👍
                    </button>
                    <button
                      type="button"
                      aria-label="Negative feedback"
                      className={
                        messageFeedback[msg.id]?.value === 'negative'
                          ? styles.feedbackSentNegative
                          : ''
                      }
                      onClick={() => handleNegativeClick(msg.id!)}
                    >
                      👎
                    </button>
                  </div>
                  {negativeFeedbackMessageId === msg.id && (
                    <div className={styles.feedbackComment}>
                      <label htmlFor={`feedback-comment-${msg.id}`}>
                        Optional message (what went wrong?)
                      </label>
                      <textarea
                        id={`feedback-comment-${msg.id}`}
                        className={styles.feedbackTextarea}
                        value={feedbackComment}
                        onChange={(e) => setFeedbackComment(e.target.value)}
                        placeholder="Optional…"
                        rows={2}
                      />
                      <button
                        type="button"
                        className={styles.feedbackSubmit}
                        onClick={() => submitNegativeFeedback(msg.id!)}
                      >
                        Submit feedback
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {error && <p className={styles.error}>{error}</p>}

        <form
          className={styles.form}
          onSubmit={(e) => {
            e.preventDefault()
            sendMessage()
          }}
        >
          <textarea
            className={styles.input}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                sendMessage()
              }
            }}
            placeholder="Ask about papers…"
            rows={2}
            disabled={loading}
          />
          <button type="submit" className={styles.send} disabled={loading || !input.trim()}>
            {loading ? 'Sending…' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}
