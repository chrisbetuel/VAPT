import { useEffect, useRef } from 'react'
import { connectWebSocket, disconnectWebSocket, subscribeToScan, unsubscribeFromScan } from '@/services/websocket'

export function useWebSocket(enabled = false) {
  const enabledRef = useRef(enabled)
  enabledRef.current = enabled

  useEffect(() => {
    if (!enabledRef.current) return
    connectWebSocket()
    return () => {
      disconnectWebSocket()
    }
  }, [enabled])
}

export function useScanSubscription(scanId: number | undefined) {
  const scanIdRef = useRef(scanId)
  scanIdRef.current = scanId

  useEffect(() => {
    if (!scanIdRef.current) return
    connectWebSocket()
    subscribeToScan(scanIdRef.current)
    return () => {
      unsubscribeFromScan(scanIdRef.current!)
    }
  }, [scanId])
}
