import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { login as apiLogin, register as apiRegister } from '../api/auth'
import type { UserCreate } from '../types/api'

const TOKEN_KEY = 'token'

interface AuthState {
  token: string | null
  ready: boolean
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (payload: UserCreate) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: localStorage.getItem(TOKEN_KEY),
    ready: false,
  })

  useEffect(() => {
    setState((s) => ({ ...s, ready: true }))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password)
    localStorage.setItem(TOKEN_KEY, access_token)
    setState({ token: access_token, ready: true })
  }, [])

  const register = useCallback(async (payload: UserCreate) => {
    await apiRegister(payload)
    const { access_token } = await apiLogin(payload.email, payload.password)
    localStorage.setItem(TOKEN_KEY, access_token)
    setState({ token: access_token, ready: true })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setState({ token: null, ready: true })
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      logout,
      isAuthenticated: !!state.token,
    }),
    [state.token, state.ready, login, register, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
