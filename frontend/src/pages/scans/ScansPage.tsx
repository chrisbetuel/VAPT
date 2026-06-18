import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { scansApi } from '@/api/scans'
import { Plus, Play, Square, Eye } from 'lucide-react'

const statusColors: Record<string, string> = {
  completed: 'bg-green-500/10 text-green-500',
  running: 'bg-blue-500/10 text-blue-500',
  pending: 'bg-yellow-500/10 text-yellow-500',
  failed: 'bg-red-500/10 text-red-500',
  cancelled: 'bg-gray-500/10 text-gray-500',
}

export default function ScansPage() {
  const queryClient = useQueryClient()
  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: scansApi.list,
    select: (res: any) => res.data,
  })

  const startMutation = useMutation({
    mutationFn: scansApi.start,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scans'] }),
  })

  const stopMutation = useMutation({
    mutationFn: scansApi.stop,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scans'] }),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Scans</h2>
        <Link
          to="/scans/new"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          New Scan
        </Link>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Target</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Progress</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {scans?.length ? (
                scans.map((scan: { id: string; name: string; target: string; status: string; progress: number }) => (
                  <tr key={scan.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-3 font-medium">{scan.name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{scan.target_name || scan.target}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[scan.status] || 'bg-gray-500/10 text-gray-500'}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${scan.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">{scan.progress}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {scan.status === 'pending' && (
                          <button
                            onClick={() => startMutation.mutate(scan.id)}
                            className="rounded p-1 text-green-500 hover:bg-green-500/10"
                            title="Start"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                        )}
                        {scan.status === 'running' && (
                          <button
                            onClick={() => stopMutation.mutate(scan.id)}
                            className="rounded p-1 text-red-500 hover:bg-red-500/10"
                            title="Stop"
                          >
                            <Square className="h-4 w-4" />
                          </button>
                        )}
                        <Link
                          to={`/scans/${scan.id}`}
                          className="rounded p-1 text-muted-foreground hover:bg-muted"
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No scans found
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
