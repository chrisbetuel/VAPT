import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { scansApi } from "@/services/api";
import type { ScanCreate } from "@/types";

export function useScans(params?: { page?: number; status?: string; target_id?: number }) {
  return useQuery({
    queryKey: ["scans", params],
    queryFn: () => scansApi.list(params),
    select: (res) => res.data,
  });
}

export function useScan(scanId: number) {
  return useQuery({
    queryKey: ["scan", scanId],
    queryFn: () => scansApi.get(scanId),
    select: (res) => res.data,
    enabled: !!scanId,
  });
}

export function useCreateScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScanCreate) => scansApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}

export function useStartScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scanId: number) => scansApi.start(scanId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}

export function useStopScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scanId: number) => scansApi.stop(scanId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}

export function useDeleteScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (scanId: number) => scansApi.delete(scanId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scans"] });
    },
  });
}
