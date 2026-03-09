import { useCallback, useRef, useState } from 'react'
import { chatStream } from '../api/chat'
import type { ChatMessage as ChatMessageType } from '../types/api'
import styles from './Chat.module.css'

function randomSessionId(): string {
  return crypto.randomUUID()
}

export function Chat() {
  const [sessionId] = useState(() => randomSessionId())
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError(null)
    const userMessage: ChatMessageType = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    const history: ChatMessageType[] = [...messages, userMessage]
    const assistantPlaceholder: ChatMessageType = { role: 'assistant', content: '' }
    setMessages((prev) => [...prev, assistantPlaceholder])

    let accumulated = ''
    try {
      for await (const chunk of chatStream(sessionId, { chat_history: history })) {
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
          scrollToBottom()
        }
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
      setMessages((prev) => prev.filter((m) => m.content !== ''))
    } finally {
      setLoading(false)
    }
  }, [input, loading, messages, sessionId, scrollToBottom])

  return (
    <div className={styles.chat}>
      <div className={styles.header}>
        <h1>arXiv Assistant</h1>
        <p className={styles.subtitle}>
          Ask questions about papers. Session: <code>{sessionId.slice(0, 8)}…</code>
        </p>
      </div>

      <div className={styles.messages} ref={bottomRef}>
        {messages.length === 0 && (
          <div className={styles.empty}>
            <p>Send a message to start. I can search and reason over arXiv papers.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={msg.role === 'user' ? styles.msgUser : styles.msgAssistant}
          >
            <span className={styles.role}>{msg.role === 'user' ? 'You' : 'Assistant'}</span>
            <div className={styles.content}>
              {msg.content || (loading && i === messages.length - 1 ? '…' : '')}
            </div>
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
  )
}
