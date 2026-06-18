import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { targetsApi } from '@/api/targets'
import { Plus } from 'lucide-react'
import toast from 'react-hot-toast'

export default function TargetsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ name: '', url: '', description: '' })

  const { data: targets, isLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: targetsApi.list,
    select: (res: any) => res.data,
  })

  const mutation = useMutation({
    mutationFn: targetsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] })
      setShowModal(false)
      setForm({ name: '', url: '', description: '' })
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to create target'
      toast.error(msg)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: targetsApi.delete,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['targets'] }),
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || err?.message || 'Failed to delete target'
      toast.error(msg)
    },
  })

  const statusColors: Record<string, string> = {
    online: 'bg-green-500/10 text-green-500',
    offline: 'bg-red-500/10 text-red-500',
    unknown: 'bg-gray-500/10 text-gray-500',
  }

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
        <h2 className="text-xl font-semibold">Targets</h2>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Add Target
        </button>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Target</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Last Scan</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {targets?.length ? (
                targets.map((t: { id: string; name: string; url: string; status: string; lastScan: string }) => (
                  <tr key={t.id} className="border-b hover:bg-muted/50">
                    <td className="px-4 py-3 font-medium">
                      <Link to={`/targets/${t.id}`} className="hover:text-primary">
                        {t.name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{t.url}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[t.status] || statusColors.unknown}`}>
                        {t.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{t.lastScan || 'Never'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/targets/${t.id}`}
                          className="text-sm text-primary hover:underline"
                        >
                          View
                        </Link>
                        <button
                          onClick={() => deleteMutation.mutate(t.id)}
                          className="text-sm text-destructive hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No targets found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-semibold">Add Target</h3>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                mutation.mutate(form)
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Target (IP or Domain)</label>
                <input
                  value={form.url}
                  onChange={(e) => setForm({ ...form, url: e.target.value })}
                  required
                  placeholder="192.168.1.1 or example.com"
                  className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="inline-flex h-10 items-center justify-center rounded-md border bg-background px-4 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={mutation.isPending}
                  className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {mutation.isPending ? 'Adding...' : 'Add Target'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
