import { apiRequest } from './client'
import type { Token } from '../types/api'
import type { UserCreate, UserOut } from '../types/api'

const base = () => import.meta.env.VITE_API_URL || ''

export async function login(email: string, password: string): Promise<Token> {
  const form = new URLSearchParams()
  form.set('username', email)
  form.set('password', password)
  const res = await fetch(`${base()}/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err.detail as string) || 'Login failed')
  }
  return res.json() as Promise<Token>
}

export async function register(payload: UserCreate): Promise<UserOut> {
  return apiRequest<UserOut>('/users/', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
