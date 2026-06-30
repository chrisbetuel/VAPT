import { useQuery } from '@tanstack/react-query'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { dashboardApi } from '@/api/dashboard'
import { Shield, Activity, Bug, Crosshair } from 'lucide-react'

const severityColors = ['#22c55e', '#eab308', '#f97316', '#ef4444']

const severityLabels = ['low', 'medium', 'high', 'critical']

const statCards = [
  { label: 'Total Scans', key: 'total_scans', icon: Shield, color: 'text-blue-500' },
  { label: 'Active Scans', key: 'active_scans', icon: Activity, color: 'text-green-500' },
  { label: 'Vulnerabilities', key: 'total_vulnerabilities', icon: Bug, color: 'text-red-500' },
  { label: 'Targets', key: 'total_targets', icon: Crosshair, color: 'text-purple-500' },
]

export default function DashboardPage() {
  const { data: statsRes, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.stats,
    select: (res: any) => res.data,
  })

  const { data: recentRes } = useQuery({
    queryKey: ['dashboard', 'recent-scans'],
    queryFn: dashboardApi.recentScans,
    select: (res: any) => res.data ?? [],
  })

  const { data: trendRes } = useQuery({
    queryKey: ['dashboard', 'trends'],
    queryFn: dashboardApi.vulnerabilityTrends,
    select: (res: any) => res.data ?? [],
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  const severityDist = statsRes?.severity_distribution ?? {}
  const pieData = severityLabels
    .filter((s) => (severityDist[s] ?? 0) > 0)
    .map((s) => ({ name: s, value: severityDist[s] ?? 0 }))

  const recentScans = Array.isArray(recentRes) ? recentRes : []
  const trendData = Array.isArray(trendRes) ? trendRes : []

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon
          return (
            <div key={card.key} className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">{card.label}</p>
                <Icon className={`h-5 w-5 ${card.color}`} />
              </div>
              <p className="mt-2 text-3xl font-bold">{statsRes?.[card.key] ?? 0}</p>
            </div>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-4 font-semibold">Severity Distribution</h3>
          <div className="h-64">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                  >
                    {pieData.map((_, idx) => (
                      <Cell key={idx} fill={severityColors[idx % severityColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                No vulnerability data
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-4 font-semibold">Vulnerability Trend (30 days)</h3>
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            {trendData.length > 0 ? (
              <div className="h-full w-full space-y-1 overflow-y-auto">
                {trendData.map((d: { date: string; count: number }, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-24 shrink-0 text-right">{d.date}</span>
                    <div className="flex-1 rounded-full bg-muted">
                      <div
                        className="h-4 rounded-full bg-primary"
                        style={{ width: `${Math.min((d.count / Math.max(...trendData.map((t: any) => t.count))) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="w-8 text-left font-medium">{d.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              'No trend data available'
            )}
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="border-b px-4 py-3">
          <h3 className="font-semibold">Recent Scans</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-2 text-left font-medium">Name</th>
                <th className="px-4 py-2 text-left font-medium">Target</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {recentScans.length > 0 ? (
                recentScans.map((scan: { id: number; name: string; target_url: string; status: string; started_at: string }) => (
                  <tr key={scan.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{scan.name}</td>
                    <td className="px-4 py-2 text-muted-foreground">{scan.target_url}</td>
                    <td className="px-4 py-2">
                      <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        {scan.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {scan.started_at ? new Date(scan.started_at).toLocaleDateString() : 'N/A'}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    No scans yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
