import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timezone

import httpx
import redis as redis_lib
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flask-webhooks")

app = Flask(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-webhook-secret")

try:
    redis_client = redis_lib.from_url(REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None
    logger.warning("Redis not available, using in-memory store")

in_memory_store: dict[str, list[dict]] = {}


def _store(key: str, data: dict):
    if redis_client:
        redis_client.lpush(key, json.dumps(data))
        redis_client.ltrim(key, 0, 499)
    else:
        in_memory_store.setdefault(key, []).insert(0, data)
        in_memory_store[key] = in_memory_store[key][:500]


def _fetch(key: str, start: int = 0, end: int = -1) -> list[dict]:
    if redis_client:
        raw = redis_client.lrange(key, start, end)
        return [json.loads(r) for r in raw]
    return in_memory_store.get(key, [])[start:end if end >= 0 else len(in_memory_store.get(key, []))]


def _verify_signature(payload: bytes, signature: str | None) -> bool:
    if not signature:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "flask-webhooks", "status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.route("/api/webhooks/receive/<source>", methods=["POST"])
def receive_webhook(source: str):
    payload = request.get_data()
    signature = request.headers.get("X-Webhook-Signature")

    if WEBHOOK_SECRET != "change-me-webhook-secret":
        if not _verify_signature(payload, signature):
            return jsonify({"error": "Invalid signature"}), 401

    data = request.get_json(silent=True) or {}
    event = {
        "source": source,
        "event": request.headers.get("X-Webhook-Event", "unknown"),
        "payload": data,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "headers": dict(request.headers),
    }
    _store(f"webhooks:{source}", event)
    logger.info("Webhook received from %s: %s", source, data.get("action", "unknown"))
    return jsonify({"status": "received", "event_id": event["received_at"]}), 202


@app.route("/api/webhooks/events", methods=["GET"])
def list_events():
    source = request.args.get("source", "all")
    limit = int(request.args.get("limit", 50))
    key = f"webhooks:{source}" if source != "all" else "webhooks:*"
    if key.endswith("*"):
        events = []
        if redis_client:
            for k in redis_client.scan_iter(match=key):
                events.extend(_fetch(k, 0, limit - len(events)))
                if len(events) >= limit:
                    break
        else:
            for k, v in in_memory_store.items():
                if k.startswith("webhooks:"):
                    events.extend(v[:limit - len(events)])
                    if len(events) >= limit:
                        break
        return jsonify({"events": events[:limit], "total": len(events)})
    return jsonify({"events": _fetch(key, 0, limit - 1), "total": len(_fetch(key))})


@app.route("/api/webhooks/deliver", methods=["POST"])
def deliver_webhook():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    payload = data.get("payload", {})
    secret = data.get("secret", WEBHOOK_SECRET)

    if not url:
        return jsonify({"error": "url is required"}), 400

    body = json.dumps(payload)
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()

    try:
        resp = httpx.post(url, content=body, headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": f"sha256={signature}",
            "User-Agent": "VAPT-Webhook/1.0",
        }, timeout=30)
        result = {
            "url": url,
            "status_code": resp.status_code,
            "success": resp.is_success,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }
        _store("webhook_deliveries", result)
        logger.info("Webhook delivered to %s: %s", url, resp.status_code)
        return jsonify(result), 202 if resp.is_success else 502
    except Exception as e:
        result = {"url": url, "error": str(e), "success": False, "delivered_at": datetime.now(timezone.utc).isoformat()}
        _store("webhook_deliveries", result)
        logger.error("Webhook delivery to %s failed: %s", url, e)
        return jsonify(result), 502


@app.route("/api/webhooks/stats", methods=["GET"])
def stats():
    delivery_count = len(_fetch("webhook_deliveries", 0, 999))
    return jsonify({
        "total_deliveries": delivery_count,
        "uptime": datetime.now(timezone.utc).isoformat(),
    })


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
