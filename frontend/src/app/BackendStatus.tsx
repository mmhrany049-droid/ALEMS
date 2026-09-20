/** Backend status dot — polls /health (proxied to 127.0.0.1:8010). */
import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '../lib/health'

export function BackendStatus({ compact = false }: { compact?: boolean }) {
  const { data, isError, isPending } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30_000,
    retry: 1,
  })

  const state = isPending ? 'pending' : isError || !data ? 'down' : 'up'
  const color = state === 'up' ? 'bg-success' : state === 'down' ? 'bg-danger' : 'bg-warning'

  return (
    <div
      className="flex items-center gap-2 rounded-md border border-border bg-surface px-2.5 py-1.5 text-body-sm"
      title={state === 'up' ? `backend v${data!.app_version} — 127.0.0.1:8010` : 'backend آفلاین است'}
    >
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      {!compact && <span className="text-muted">{state === 'up' ? 'متصل' : state === 'down' ? 'آفلاین' : '…'}</span>}
    </div>
  )
}
