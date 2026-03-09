import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { fetchMetadata } from '../api/ingestion'
import { openTaskStream } from '../api/tasks'
import type { TaskStatusResponse } from '../types/api'
import styles from './Ingestion.module.css'

function parsePaperIds(raw: string): string[] {
  return raw
    .split(/[\n,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

export function Ingestion() {
  const queryClient = useQueryClient()
  const [paperIdsRaw, setPaperIdsRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastTaskId, setLastTaskId] = useState<string | null>(null)
  const [streamStatus, setStreamStatus] = useState<TaskStatusResponse | null>(null)
  const [streamError, setStreamError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const ids = parsePaperIds(paperIdsRaw)
    if (ids.length === 0) {
      setError('Enter at least one arXiv ID (e.g. 2401.12345 or 2401.12345v2)')
      return
    }
    if (ids.length > 20) {
      setError('Maximum 20 paper IDs per request')
      return
    }
    setError(null)
    setStreamStatus(null)
    setStreamError(null)
    setLoading(true)
    try {
      const { task_id } = await fetchMetadata({
        paper_ids: ids,
        process_pdfs: true,
        store_to_db: true,
      })
      setLastTaskId(task_id)
      setStreamStatus({ task_id, status: 'queued' })
      openTaskStream(
        task_id,
        (data) => setStreamStatus(data),
        (err) => setStreamError(err),
        () => {
          setLoading(false)
          queryClient.invalidateQueries({ queryKey: ['tasks'] })
        }
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ingestion failed')
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Ingestion pipeline</h1>
        <p className={styles.subtitle}>
          Submit arXiv paper IDs to fetch metadata, process PDFs, and store in the database.
          Tasks run asynchronously.
        </p>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.field}>
          <label htmlFor="paperIds">arXiv paper IDs (one per line or comma-separated)</label>
          <textarea
            id="paperIds"
            value={paperIdsRaw}
            onChange={(e) => setPaperIdsRaw(e.target.value)}
            placeholder="2401.12345&#10;2402.00001v2"
            rows={5}
            className={styles.textarea}
          />
        </div>
        {error && <p className={styles.error}>{error}</p>}
        <button type="submit" className={styles.submit} disabled={loading}>
          {loading ? 'Submitting…' : 'Start ingestion'}
        </button>
      </form>

      {(lastTaskId || streamStatus) && (
        <div className={styles.result}>
          <h2>Latest task</h2>
          <p className={styles.taskId}>
            Task ID: <code>{lastTaskId ?? streamStatus?.task_id}</code>
          </p>
          {streamStatus && (
            <p className={styles.status}>
              Status: <strong>{streamStatus.status}</strong>
              {streamStatus.db_status && ` (${streamStatus.db_status})`}
            </p>
          )}
          {streamError && <p className={styles.error}>{streamError}</p>}
          {streamStatus?.result != null && (
            <pre className={styles.pre}>{JSON.stringify(streamStatus.result, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  )
}
