import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { listRecoveryIssues } from '../api/recovery'

export default function RecoveryIndicator() {
  const [count, setCount] = useState(0)

  const refresh = useCallback(() => {
    listRecoveryIssues()
      .then((data) => setCount(data.active_count || 0))
      .catch(() => setCount(0))
  }, [])

  useEffect(() => {
    refresh()
    window.addEventListener('app:recovery-refresh', refresh)
    return () => window.removeEventListener('app:recovery-refresh', refresh)
  }, [refresh])

  if (!count) return null
  return (
    <a className="recovery-indicator" role="status" href="#/settings/recovery" aria-label={`${count} 个问题待处理`}>
      <AlertTriangle size={16} aria-hidden="true" />
      <span>{count} 个问题待处理</span>
    </a>
  )
}
