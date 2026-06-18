import { create } from "zustand";
import type { Scan, ScanLog, WsScanProgress, WsVulnerabilityFound } from "@/types";

interface ScanState {
  activeScans: Map<number, Scan>;
  scanProgress: Map<number, WsScanProgress>;
  scanLogs: Map<number, ScanLog[]>;
  addActiveScan: (scan: Scan) => void;
  updateScanProgress: (progress: WsScanProgress) => void;
  addVulnerability: (scanId: number, vuln: WsVulnerabilityFound) => void;
  addScanLog: (scanId: number, log: ScanLog) => void;
  removeScan: (scanId: number) => void;
  clearCompleted: () => void;
}

export const useScanStore = create<ScanState>()((set, get) => ({
  activeScans: new Map(),
  scanProgress: new Map(),
  scanLogs: new Map(),

  addActiveScan: (scan) => {
    const activeScans = new Map(get().activeScans);
    activeScans.set(scan.id, scan);
    set({ activeScans });
  },

  updateScanProgress: (progress) => {
    const scanProgress = new Map(get().scanProgress);
    scanProgress.set(progress.scan_id, progress);
    set({ scanProgress });
  },

  addVulnerability: (scanId, vuln) => {
    const activeScans = new Map(get().activeScans);
    const scan = activeScans.get(scanId);
    if (scan) {
      scan.vulnerabilities.push(vuln.vulnerability);
      activeScans.set(scanId, scan);
      set({ activeScans });
    }
  },

  addScanLog: (scanId, log) => {
    const scanLogs = new Map(get().scanLogs);
    const existing = scanLogs.get(scanId) ?? [];
    scanLogs.set(scanId, [...existing, log]);
    set({ scanLogs });
  },

  removeScan: (scanId) => {
    const activeScans = new Map(get().activeScans);
    const scanProgress = new Map(get().scanProgress);
    const scanLogs = new Map(get().scanLogs);
    activeScans.delete(scanId);
    scanProgress.delete(scanId);
    scanLogs.delete(scanId);
    set({ activeScans, scanProgress, scanLogs });
  },

  clearCompleted: () => {
    const activeScans = new Map(get().activeScans);
    const scanProgress = new Map(get().scanProgress);
    const scanLogs = new Map(get().scanLogs);
    for (const [id, scan] of activeScans) {
      if (scan.status === "completed" || scan.status === "error") {
        activeScans.delete(id);
        scanProgress.delete(id);
        scanLogs.delete(id);
      }
    }
    set({ activeScans, scanProgress, scanLogs });
  },
}));
