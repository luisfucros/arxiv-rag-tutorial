const getBaseUrl = () => import.meta.env.VITE_API_URL || ''

/** FastAPI often returns `detail` as a string or a validation error list. */
function formatDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = 'loc' in item && Array.isArray((item as { loc: unknown }).loc)
            ? (item as { loc: string[] }).loc.join('.') + ': '
            : ''
          return loc + String((item as { msg: string }).msg)
        }
        return JSON.stringify(item)
      })
      .join('; ')
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: string }).message)
  }
  return ''
}

export function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token')
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getBaseUrl()}${path}`
  const res = await fetch(url, {
    ...options,
    headers: {
      ...getAuthHeaders(),
      ...(options.headers as Record<string, string>),
    },
  })
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}))
    const msg = formatDetail(errBody.detail) || res.statusText
    throw new ApiError(res.status, msg)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
