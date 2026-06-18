import { useState, useMemo, useRef, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { scansApi } from '@/api/scans'
import { useScanStore } from '@/stores/scanStore'
import { useScanSubscription } from '@/hooks/useWebSocket'
import type { Scan } from '@/types'

type Tab = 'overview' | 'vulnerabilities' | 'logs' | 'reports'

export default function ScanDetailPage() {
  const { id } = useParams<{ id: string }>()
  const scanId = Number(id)
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  const scanProgress = useScanStore((state) => state.scanProgress.get(scanId))
  const liveVulns = useScanStore((state) => state.activeScans.get(scanId)?.vulnerabilities ?? [])
  const liveLogs = useScanStore((state) => state.scanLogs.get(scanId) ?? [])
  const logsEndRef = useRef<HTMLDivElement>(null)

  useScanSubscription(scanId)

  const { data: scan, isLoading } = useQuery({
    queryKey: ['scan', id],
    queryFn: () => scansApi.get(scanId),
    select: (res: any) => res.data as Scan,
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data as Scan | undefined
      if (data?.status === 'running' || data?.status === 'pending') return 3000
      return false
    },
  })

  const progress = scanProgress?.progress ?? scan?.progress ?? 0
  const displayStatus = scanProgress?.status ?? scan?.status ?? ''

  const mergedVulnerabilities = useMemo(() => {
    if (!scan) return liveVulns
    const apiVulns = scan.vulnerabilities ?? []
    const apiIds = new Set(apiVulns.map((v) => v.id))
    const newFromLive = liveVulns.filter((v) => !apiIds.has(v.id))
    return [...apiVulns, ...newFromLive]
  }, [scan, liveVulns])

  const mergedLogs = useMemo(() => {
    if (!scan) return liveLogs
    const apiLogs = scan.logs ?? []
    const apiKeys = new Set(apiLogs.map((l) => l.created_at ?? l.id))
    const newFromLive = liveLogs.filter((l) => !apiKeys.has(l.created_at ?? l.id))
    return [...apiLogs, ...newFromLive]
  }, [scan, liveLogs])

  useEffect(() => {
    if (activeTab === 'logs') {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [mergedLogs.length, activeTab])

  const tabs: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'vulnerabilities', label: `Vulnerabilities (${mergedVulnerabilities.length})` },
    { key: 'logs', label: `Logs (${mergedLogs.length})` },
    { key: 'reports', label: 'Reports' },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Scan not found
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">{scan.name}</h2>
          <p className="text-sm text-muted-foreground">Target ID: {scan.target_id}</p>
        </div>
        <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium capitalize ${
          displayStatus === 'running' ? 'bg-blue-500/10 text-blue-500' :
          displayStatus === 'completed' ? 'bg-green-500/10 text-green-500' :
          displayStatus === 'error' ? 'bg-red-500/10 text-red-500' :
          displayStatus === 'cancelled' ? 'bg-gray-500/10 text-gray-500' :
          'bg-yellow-500/10 text-yellow-500'
        }`}>
          {displayStatus}
        </span>
      </div>

      {(displayStatus === 'running' || displayStatus === 'pending') && (
        <div className="space-y-2 rounded-lg border bg-card p-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Scan Progress</span>
            <span>{progress.toFixed(1)}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          {scanProgress?.message && (
            <p className="text-xs text-muted-foreground">{scanProgress.message}</p>
          )}
        </div>
      )}

      <div className="border-b">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`border-b-2 px-1 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        {activeTab === 'overview' && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm text-muted-foreground">Status</p>
              <p className="mt-1 text-lg font-semibold capitalize">{displayStatus}</p>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm text-muted-foreground">Vulnerabilities</p>
              <p className="mt-1 text-lg font-semibold">{mergedVulnerabilities?.length ?? 0}</p>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm text-muted-foreground">Type</p>
              <p className="mt-1 text-lg font-semibold">{(scan.config as any)?.scan_type ?? 'N/A'}</p>
            </div>
            <div className="rounded-lg border bg-card p-4">
              <p className="text-sm text-muted-foreground">Intensity</p>
              <p className="mt-1 text-lg font-semibold">{(scan.config as any)?.intensity ?? 'N/A'}</p>
            </div>
          </div>
        )}

        {activeTab === 'vulnerabilities' && (
          <div className="rounded-lg border bg-card">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-2 text-left font-medium">Severity</th>
                    <th className="px-4 py-2 text-left font-medium">Title</th>
                    <th className="px-4 py-2 text-left font-medium">CVSS</th>
                    <th className="px-4 py-2 text-left font-medium">CVE</th>
                  </tr>
                </thead>
                <tbody>
                  {mergedVulnerabilities.length ? (
                    mergedVulnerabilities.map((vuln) => (
                      <tr key={vuln.id ?? vuln.title} className="border-b hover:bg-muted/50">
                        <td className="px-4 py-2">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            vuln.severity === 'critical' ? 'bg-red-500/10 text-red-500' :
                            vuln.severity === 'high' ? 'bg-orange-500/10 text-orange-500' :
                            vuln.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
                            'bg-green-500/10 text-green-500'
                          }`}>
                            {vuln.severity}
                          </span>
                        </td>
                        <td className="px-4 py-2 font-medium">{vuln.title}</td>
                        <td className="px-4 py-2 text-muted-foreground">{vuln.cvss_score ?? 'N/A'}</td>
                        <td className="px-4 py-2">{vuln.cve_id ?? 'N/A'}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                        No vulnerabilities found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="rounded-lg border bg-card">
            <div className="max-h-96 overflow-y-auto p-4 font-mono text-xs">
              {mergedLogs.length ? (
                mergedLogs.map((log, idx) => (
                  <div key={log.id ?? idx} className={`py-0.5 ${
                    log.level === 'WARNING' || log.level === 'ERROR' ? 'text-red-400' :
                    log.level === 'INFO' ? 'text-foreground' :
                    'text-muted-foreground'
                  }`}>
                    <span className="text-muted-foreground">
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}
                    </span>{' '}
                    {log.scanner && <span className="font-semibold">[{log.scanner}]</span>}{' '}
                    {log.message}
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground">
                  {displayStatus === 'running' || displayStatus === 'pending'
                    ? 'Waiting for scan logs...'
                    : 'No logs available'}
                </p>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            Report generation options will appear here.
          </div>
        )}
      </div>
    </div>
  )
}
