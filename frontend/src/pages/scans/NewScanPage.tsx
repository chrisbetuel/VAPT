import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { scansApi } from '@/api/scans'
import { targetsApi } from '@/api/targets'

interface NewScanForm {
  name: string
  description: string
  targetId: string
  scanType: string
  intensity: string
  scanners: string[]
}

const scannerOptions = [
  { value: 'zap', label: 'OWASP ZAP (Web App)' },
  { value: 'nuclei', label: 'Nuclei (CVE Templates)' },
  { value: 'nmap', label: 'Nmap (Port Scan)' },
  { value: 'subfinder', label: 'Subfinder (Subdomains)' },
  { value: 'ffuf', label: 'FFUF (Directory Fuzzing)' },
]

export default function NewScanPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState<NewScanForm>({
    name: '',
    description: '',
    targetId: '',
    scanType: 'quick',
    intensity: 'normal',
    scanners: ['zap', 'nmap'],
  })

  const { data: targetsRes } = useQuery({
    queryKey: ['targets'],
    queryFn: targetsApi.list,
  })
  const targets = (targetsRes as any)?.data ?? []

  const mutation = useMutation({
    mutationFn: scansApi.create,
    onSuccess: (res) => {
      const data = (res as any)?.data ?? res
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      navigate(`/scans/${data.id}`)
    },
  })

  const toggleScanner = (value: string) => {
    setForm((prev) => ({
      ...prev,
      scanners: prev.scanners.includes(value)
        ? prev.scanners.filter((s) => s !== value)
        : [...prev.scanners, value],
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate({
      target_id: parseInt(form.targetId),
      name: form.name,
      description: form.description || undefined,
      config: {
        scan_type: form.scanType,
        scanners: form.scanners,
        intensity: form.intensity,
      },
    })
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h2 className="text-xl font-semibold">New Scan</h2>

      <form onSubmit={handleSubmit} className="space-y-6 rounded-lg border bg-card p-6">
        <div className="space-y-2">
          <label htmlFor="name" className="text-sm font-medium">Scan Name</label>
          <input
            id="name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="description" className="text-sm font-medium">Description</label>
          <textarea
            id="description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
            className="flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="targetId" className="text-sm font-medium">Target</label>
          <select
            id="targetId"
            value={form.targetId}
            onChange={(e) => setForm({ ...form, targetId: e.target.value })}
            required
            className="flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">Select a target...</option>
            {targets.map((t: { id: string; name: string; url: string }) => (
              <option key={t.id} value={t.id}>
                {t.name} ({t.url})
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Scan Type</label>
          <div className="flex gap-4">
            {['quick', 'full', 'custom'].map((type) => (
              <label key={type} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="scanType"
                  value={type}
                  checked={form.scanType === type}
                  onChange={(e) => setForm({ ...form, scanType: e.target.value })}
                  className="text-primary"
                />
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Intensity</label>
          <div className="flex gap-4">
            {['light', 'normal', 'aggressive'].map((level) => (
              <label key={level} className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="intensity"
                  value={level}
                  checked={form.intensity === level}
                  onChange={(e) => setForm({ ...form, intensity: e.target.value })}
                  className="text-primary"
                />
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Scanners</label>
          <div className="grid grid-cols-2 gap-2">
            {scannerOptions.map((scanner) => (
              <label
                key={scanner.value}
                className={`flex cursor-pointer items-center gap-2 rounded-md border p-3 text-sm transition-colors ${
                  form.scanners.includes(scanner.value)
                    ? 'border-primary bg-primary/5'
                    : 'hover:bg-muted'
                }`}
              >
                <input
                  type="checkbox"
                  checked={form.scanners.includes(scanner.value)}
                  onChange={() => toggleScanner(scanner.value)}
                  className="text-primary"
                />
                {scanner.label}
              </label>
            ))}
          </div>
        </div>

        {mutation.error && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : 'Failed to create scan'}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {mutation.isPending ? 'Creating...' : 'Create Scan'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/scans')}
            className="inline-flex h-10 items-center justify-center rounded-md border bg-background px-6 text-sm font-medium hover:bg-muted"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
