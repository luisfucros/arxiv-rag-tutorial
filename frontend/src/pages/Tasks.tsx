import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listTasks, retryTask } from '../api/tasks'
import styles from './Tasks.module.css'

export function Tasks() {
  const queryClient = useQueryClient()
  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ['tasks'],
    queryFn: listTasks,
  })
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
          {tasks?.map((t) => (
            <li key={t.task_id} className={styles.item}>
              <code className={styles.taskId}>{t.task_id}</code>
              <span className={styles.status} data-status={t.status}>
                {t.status}
              </span>
              {['FAILURE', 'REVOKED', 'REJECTED'].includes(t.status) && (
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
          ))}
        </ul>
      )}
    </div>
  )
}
