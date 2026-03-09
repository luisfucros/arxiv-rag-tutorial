import { useEffect, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listTasks, openTaskStream, retryTask } from '../api/tasks'
import type { TaskStatusResponse } from '../types/api'
import styles from './Tasks.module.css'

const IN_PROGRESS = ['pending', 'running', 'PENDING', 'STARTED']

function isInProgress(status: string): boolean {
  return IN_PROGRESS.includes(status)
}

export function Tasks() {
  const queryClient = useQueryClient()
  const [liveStatus, setLiveStatus] = useState<Record<string, TaskStatusResponse>>({})
  const streamCleanupsRef = useRef<Record<string, () => void>>({})

  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: listTasks,
  })

  useEffect(() => {
    if (!tasks?.length) return
    tasks.forEach((t) => {
      if (!isInProgress(t.status)) return
      if (streamCleanupsRef.current[t.task_id]) return
      const cleanup = openTaskStream(
        t.task_id,
        (data) => {
          setLiveStatus((prev) => ({ ...prev, [t.task_id]: data }))
        },
        () => {},
        () => {
          queryClient.invalidateQueries({ queryKey: ['tasks'] })
          setLiveStatus((prev) => {
            const next = { ...prev }
            delete next[t.task_id]
            return next
          })
          delete streamCleanupsRef.current[t.task_id]
        }
      )
      streamCleanupsRef.current[t.task_id] = cleanup
    })
    return () => {
      Object.values(streamCleanupsRef.current).forEach((fn) => fn())
      streamCleanupsRef.current = {}
    }
  }, [tasks, queryClient])

  const retry = useMutation({
    mutationFn: retryTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })

  if (isLoading) return <div className="page-loading">Loading tasks…</div>
  if (error) {
    return (
      <p className={styles.error}>
        Failed to load tasks: {error instanceof Error ? error.message : String(error)}
      </p>
    )
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Tasks</h1>
        <p className={styles.subtitle}>Background ingestion and processing tasks.</p>
      </div>

      {tasks?.length === 0 ? (
        <p className={styles.empty}>No tasks yet. Start an ingestion from the Ingestion page.</p>
      ) : (
        <ul className={styles.list}>
          {tasks?.map((t) => {
            const display = liveStatus[t.task_id] ?? t
            const status = display.status
            return (
              <li key={t.task_id} className={styles.item}>
                <code className={styles.taskId}>{t.task_id}</code>
                <span className={styles.status} data-status={status}>
                  {status}
                </span>
                {['failed', 'FAILURE', 'REVOKED', 'REJECTED'].includes(status) && (
                  <button
                    type="button"
                    className={styles.retry}
                    onClick={() => retry.mutate(t.task_id)}
                    disabled={retry.isPending}
                  >
                    {retry.isPending ? 'Retrying…' : 'Retry'}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
