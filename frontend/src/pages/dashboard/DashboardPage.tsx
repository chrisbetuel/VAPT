import { useQuery } from '@tanstack/react-query'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { dashboardApi } from '@/api/dashboard'
import { Shield, Activity, Bug, Crosshair } from 'lucide-react'

const severityColors = ['#22c55e', '#eab308', '#f97316', '#ef4444']

const statCards = [
  { label: 'Total Scans', key: 'totalScans', icon: Shield, color: 'text-blue-500' },
  { label: 'Active Scans', key: 'activeScans', icon: Activity, color: 'text-green-500' },
  { label: 'Vulnerabilities', key: 'vulnerabilities', icon: Bug, color: 'text-red-500' },
  { label: 'Targets', key: 'targets', icon: Crosshair, color: 'text-purple-500' },
]

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getStats,
    select: (res: any) => res.data,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

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
              <p className="mt-2 text-3xl font-bold">{data?.[card.key] ?? 0}</p>
            </div>
          )
        })}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-4 font-semibold">Severity Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.severityDistribution ?? []}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {(data?.severityDistribution ?? []).map((_: unknown, idx: number) => (
                    <Cell key={idx} fill={severityColors[idx % severityColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-lg border bg-card p-4">
          <h3 className="mb-4 font-semibold">Vulnerability Trend</h3>
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            {data?.trend ? (
              <pre className="text-xs">{JSON.stringify(data.trend, null, 2)}</pre>
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
              {data?.recentScans?.length ? (
                data.recentScans.map((scan: { id: string; name: string; target: string; status: string; createdAt: string }) => (
                  <tr key={scan.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-2">{scan.name}</td>
                    <td className="px-4 py-2 text-muted-foreground">{scan.target}</td>
                    <td className="px-4 py-2">
                      <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        {scan.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">{scan.createdAt}</td>
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
