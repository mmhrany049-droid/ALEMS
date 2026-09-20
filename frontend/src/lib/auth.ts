/**
 * Token storage — phase-1 spec: memory + localStorage با استراتژی ساده.
 * memory = fast path در session جاری؛ localStorage = دوام بین reload.
 * logout → هر دو پاک می‌شوند.
 */
const TOKEN_KEY = 'alems.token'

let memoryToken: string | null = null

export function getStoredToken(): string | null {
  if (memoryToken) return memoryToken
  try {
    const t = localStorage.getItem(TOKEN_KEY)
    if (t) memoryToken = t
    return t
  } catch {
    return null
  }
}

export function storeToken(token: string): void {
  memoryToken = token
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    /* storage unavailable — memory only */
  }
}

export function clearToken(): void {
  memoryToken = null
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore */
  }
}
