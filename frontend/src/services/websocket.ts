import { io, Socket } from "socket.io-client";
import { useAuthStore } from "@/stores/authStore";
import { useScanStore } from "@/stores/scanStore";
import type {
  WsScanProgress,
  WsVulnerabilityFound,
  WsScanLog,
} from "@/types";

const WS_URL = import.meta.env.VITE_WS_URL || "http://localhost:8000";

let socket: Socket | null = null;

export function connectWebSocket(): Socket {
  const { tokens } = useAuthStore.getState();

  if (socket?.connected) return socket;

  socket = io(WS_URL, {
    auth: { token: tokens?.access_token },
    transports: ["websocket"],
    reconnection: true,
    reconnectionAttempts: 10,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 10000,
  });

  socket.on("connect", () => {
    console.log("[WS] Connected:", socket?.id);
  });

  socket.on("scan:progress", (data: WsScanProgress) => {
    useScanStore.getState().updateScanProgress(data);
  });

  socket.on("scan:vulnerability", (data: WsVulnerabilityFound) => {
    useScanStore.getState().addVulnerability(data.scan_id, data);
  });

  socket.on("scan:log", (data: WsScanLog) => {
    const log = {
      id: Date.now() + Math.random(),
      scan_id: data.scan_id,
      level: data.level,
      message: data.message,
      scanner: data.scanner,
      created_at: (data as any).created_at ?? data.timestamp ?? new Date().toISOString(),
    }
    useScanStore.getState().addScanLog(data.scan_id, log);
  });

  socket.on("disconnect", (reason) => {
    console.log("[WS] Disconnected:", reason);
  });

  socket.on("connect_error", (error) => {
    console.error("[WS] Connection error:", error.message);
  });

  return socket;
}

export function disconnectWebSocket(): void {
  if (socket) {
    socket.removeAllListeners();
    socket.disconnect();
    socket = null;
  }
}

export function subscribeToScan(scanId: number): void {
  socket?.emit("subscribe:scan", { scan_id: scanId });
}

export function unsubscribeFromScan(scanId: number): void {
  socket?.emit("unsubscribe:scan", { scan_id: scanId });
}

export function getSocket(): Socket | null {
  return socket;
}
