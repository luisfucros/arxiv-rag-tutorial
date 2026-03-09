import { useQuery } from '@tanstack/react-query'
import { listPapers } from '../api/papers'
import styles from './Papers.module.css'

export function Papers() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['papers', 0],
    queryFn: () => listPapers(50, 0),
  })

  if (isLoading) return <div className="page-loading">Loading papers…</div>
  if (error) {
    return (
      <p className={styles.error}>
        Failed to load: {error instanceof Error ? error.message : String(error)}
      </p>
    )
  }

  const papers = data?.papers ?? []
  const total = data?.total ?? 0

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1>Papers in database</h1>
        <p className={styles.subtitle}>
          Papers indexed and available for search. Total: {total}
        </p>
      </div>

      {papers.length === 0 ? (
        <p className={styles.empty}>No papers yet. Use the Ingestion pipeline to add papers.</p>
      ) : (
        <ul className={styles.list}>
          {papers.map((p) => (
            <li key={p.id} className={styles.item}>
              <a
                href={p.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.link}
              >
                {p.title}
              </a>
              <span className={styles.meta}>
                {p.arxiv_id} · {p.authors.slice(0, 2).join(', ')}
                {p.authors.length > 2 ? '…' : ''}
              </span>
              {p.pdf_processed && <span className={styles.badge}>PDF processed</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
