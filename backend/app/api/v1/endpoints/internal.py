from fastapi import APIRouter
from app.core.websocket import emit_scan_progress, emit_scan_vulnerability, emit_scan_log

router = APIRouter()


@router.post("/ws-emit")
async def ws_emit(event: str, data: dict):
    scan_id = data.get("scan_id")
    if not scan_id:
        return {"ok": False, "error": "scan_id required"}

    if event == "scan:progress":
        await emit_scan_progress(
            scan_id=scan_id,
            status=data.get("status", "running"),
            progress=data.get("progress", 0.0),
            message=data.get("message"),
        )
    elif event == "scan:vulnerability":
        await emit_scan_vulnerability(
            scan_id=scan_id,
            vulnerability=data.get("vulnerability", {}),
        )
    elif event == "scan:log":
        await emit_scan_log(
            scan_id=scan_id,
            level=data.get("level", "INFO"),
            message=data.get("message", ""),
            scanner=data.get("scanner"),
        )
    else:
        return {"ok": False, "error": f"Unknown event: {event}"}

    return {"ok": True}
