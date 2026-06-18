import socketio
from app.core.security import decode_token

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid, environ, auth):
    if not auth or "token" not in auth:
        raise ConnectionRefusedError("Authentication required")
    payload = decode_token(auth["token"])
    if not payload or "sub" not in payload:
        raise ConnectionRefusedError("Invalid token")
    return True


@sio.event
async def subscribe_scan(sid, data):
    scan_id = data.get("scan_id")
    if scan_id:
        sio.enter_room(sid, f"scan:{scan_id}")


@sio.event
async def unsubscribe_scan(sid, data):
    scan_id = data.get("scan_id")
    if scan_id:
        sio.leave_room(sid, f"scan:{scan_id}")


@sio.event
async def disconnect(sid):
    pass


async def emit_scan_progress(
    scan_id: int, status: str, progress: float, message: str | None = None
):
    await sio.emit(
        "scan:progress",
        {"scan_id": scan_id, "status": status, "progress": progress, "message": message},
        room=f"scan:{scan_id}",
    )


async def emit_scan_vulnerability(scan_id: int, vulnerability: dict):
    await sio.emit(
        "scan:vulnerability",
        {"scan_id": scan_id, "vulnerability": vulnerability},
        room=f"scan:{scan_id}",
    )


async def emit_scan_log(scan_id: int, level: str, message: str, scanner: str | None = None):
    from datetime import datetime, timezone

    await sio.emit(
        "scan:log",
        {
            "scan_id": scan_id,
            "level": level,
            "message": message,
            "scanner": scanner,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        room=f"scan:{scan_id}",
    )
