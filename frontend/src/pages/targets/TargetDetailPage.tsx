import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { targetsApi } from '@/api/targets'
import { scansApi } from '@/api/scans'
import { Plus, Play } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TargetDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: target, isLoading } = useQuery({
    queryKey: ['target', id],
    queryFn: () => targetsApi.get(id!),
    select: (res: any) => res.data,
    enabled: !!id,
  })

  const { data: scansRes } = useQuery({
    queryKey: ['scans', 'byTarget', id],
    queryFn: () => scansApi.list({ target_id: id }),
    select: (res: any) => res.data,
    enabled: !!id,
  })
  const scans = (scansRes as any)?.items ?? []

  const runScanMutation = useMutation({
    mutationFn: async () => {
      const createRes = await scansApi.create({
        target_id: Number(id),
        name: `Scan - ${target?.name ?? id}`,
        config: { scan_type: 'quick', scanners: ['zap', 'nmap'], intensity: 'normal' },
      })
      const newScan = (createRes as any).data
      await scansApi.start(newScan.id)
      return newScan
    },
    onSuccess: (newScan) => {
      queryClient.invalidateQueries({ queryKey: ['scans', 'byTarget', id] })
      navigate(`/scans/${newScan.id}`)
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to run scan'
      toast.error(msg)
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!target) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Target not found
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold">{target.name}</h2>
          <p className="font-mono text-sm text-muted-foreground">{target.url}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => runScanMutation.mutate()}
            disabled={runScanMutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            <Play className="h-4 w-4" />
            {runScanMutation.isPending ? 'Running...' : 'Run Scan'}
          </button>
          <Link
            to={`/scans/new?targetId=${id}`}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Scan
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Status</p>
          <p className="mt-1 text-lg font-semibold capitalize">{target.status}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Total Scans</p>
          <p className="mt-1 text-lg font-semibold">{scans?.length ?? 0}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Last Scan</p>
          <p className="mt-1 text-lg font-semibold">{target.last_scanned_at || 'Never'}</p>
        </div>
      </div>

      {target.description && (
        <div className="rounded-lg border bg-card p-4">
          <p className="text-sm text-muted-foreground">Description</p>
          <p className="mt-1">{target.description}</p>
        </div>
      )}

      <div className="rounded-lg border bg-card">
        <div className="border-b px-4 py-3">
          <h3 className="font-semibold">Associated Scans</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-2 text-left font-medium">Name</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Date</th>
                <th className="px-4 py-2 text-left font-medium" />
              </tr>
            </thead>
            <tbody>
              {scans?.length ? (
                scans.map((scan: { id: string; name: string; status: string; created_at: string }) => (
                  <tr key={scan.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{scan.name}</td>
                    <td className="px-4 py-2">
                      <span className="inline-flex rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                        {scan.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">{scan.created_at}</td>
                    <td className="px-4 py-2">
                      <Link
                        to={`/scans/${scan.id}`}
                        className="text-sm text-primary hover:underline"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    No scans for this target
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
