import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './Layout.module.css'

export function Layout() {
  const { logout, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className={styles.wrapper}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>
          arXiv RAG
        </Link>
        {isAuthenticated ? (
          <nav className={styles.nav}>
            <NavLink to="/" end>Chat</NavLink>
            <NavLink to="/ingestion">Ingestion</NavLink>
            <NavLink to="/tasks">Tasks</NavLink>
            <NavLink to="/papers">Papers</NavLink>
            <button type="button" onClick={handleLogout} className={styles.logout}>
              Log out
            </button>
          </nav>
        ) : (
          <nav className={styles.nav}>
            <NavLink to="/login">Sign in</NavLink>
            <NavLink to="/register">Create account</NavLink>
          </nav>
        )}
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
