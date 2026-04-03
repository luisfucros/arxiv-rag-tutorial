import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'
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
  const queryClient = useQueryClient()
  const [state, setState] = useState<AuthState>({
    token: localStorage.getItem(TOKEN_KEY),
    ready: false,
  })

  const clearUserScopedQueries = useCallback(() => {
    queryClient.removeQueries({ queryKey: ['chat-sessions'] })
    queryClient.removeQueries({ queryKey: ['tasks'] })
    queryClient.removeQueries({ queryKey: ['papers'] })
  }, [queryClient])

  useEffect(() => {
    setState((s) => ({ ...s, ready: true }))
  }, [])

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiLogin(email, password)
      clearUserScopedQueries()
      localStorage.setItem(TOKEN_KEY, access_token)
      setState({ token: access_token, ready: true })
    },
    [clearUserScopedQueries]
  )

  const register = useCallback(
    async (payload: UserCreate) => {
      await apiRegister(payload)
      const { access_token } = await apiLogin(payload.email, payload.password)
      clearUserScopedQueries()
      localStorage.setItem(TOKEN_KEY, access_token)
      setState({ token: access_token, ready: true })
    },
    [clearUserScopedQueries]
  )

  const logout = useCallback(() => {
    clearUserScopedQueries()
    localStorage.removeItem(TOKEN_KEY)
    setState({ token: null, ready: true })
  }, [clearUserScopedQueries])

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
