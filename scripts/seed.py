import asyncio
import uuid
from datetime import datetime, timedelta
from random import choice, randint, uniform

import asyncpg

DATABASE_URL = "postgresql://vapt:vapt-secret-password@localhost:5432/vapt"

SEVERITIES = ["critical", "high", "medium", "low"]
TARGET_URLS = [
    "https://example.com",
    "https://test-app.internal",
    "https://api.partner-service.com",
    "https://admin.dashboard.local",
    "https://legacy-portal.example.org",
]
TARGET_NAMES = [
    "Example Corp Main Site",
    "Internal Test Application",
    "Partner API Gateway",
    "Admin Dashboard",
    "Legacy Portal",
]


async def seed():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        admin_id = await conn.fetchval(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES ($1, $2, $3, $4) RETURNING id",
            "admin@vapt.local",
            "$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5y8z9v3r6t7u8i9o0p1a2s3d4",
            "admin",
            True,
        )
        print(f"Created admin user: {admin_id}")

        target_ids = []
        for i, (name, url) in enumerate(zip(TARGET_NAMES, TARGET_URLS)):
            tid = await conn.fetchval(
                "INSERT INTO targets (name, url, type, status, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
                name,
                url,
                choice(["web", "api", "internal", "external"]),
                "active",
                datetime.utcnow() - timedelta(days=randint(1, 30)),
                datetime.utcnow(),
            )
            target_ids.append(tid)
            print(f"Created target: {name} ({tid})")

        scan_types = ["full", "quick", "vulnerability", "compliance"]
        for target_id in target_ids:
            for _ in range(randint(2, 5)):
                scan_id = uuid.uuid4()
                start_time = datetime.utcnow() - timedelta(
                    days=randint(1, 14), hours=randint(0, 23)
                )
                duration_minutes = uniform(5, 120)
                end_time = start_time + timedelta(minutes=duration_minutes)
                status = choice(["completed", "completed", "completed", "failed"])

                await conn.execute(
                    "INSERT INTO scans (id, target_id, scan_type, status, started_at, completed_at, duration_seconds, created_by) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                    scan_id,
                    target_id,
                    choice(scan_types),
                    status,
                    start_time,
                    end_time if status == "completed" else None,
                    int(duration_minutes * 60) if status == "completed" else None,
                    admin_id,
                )

                if status == "completed":
                    vuln_count = randint(0, 15)
                    for _ in range(vuln_count):
                        severity = choice(SEVERITIES)
                        await conn.execute(
                            "INSERT INTO vulnerabilities (scan_id, target_id, name, severity, description, remediation, cvss_score, cve_id, discovered_at, status) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
                            scan_id,
                            target_id,
                            choice(
                                [
                                    "SQL Injection",
                                    "XSS Vulnerability",
                                    "Weak Cipher Suite",
                                    "Open Port",
                                    "Information Disclosure",
                                    "CSRF",
                                    "Broken Authentication",
                                    "Insecure Deserialization",
                                ]
                            ),
                            severity,
                            f"Description for vulnerability found on {url}",
                            "Apply appropriate security patches and configuration changes.",
                            round(uniform(2.0, 10.0), 1),
                            f"CVE-2024-{randint(1000, 9999)}",
                            start_time + timedelta(minutes=uniform(0, duration_minutes)),
                            choice(["open", "open", "open", "resolved", "false_positive"]),
                        )

                    for _ in range(randint(1, 20)):
                        await conn.execute(
                            "INSERT INTO scan_logs (scan_id, target_id, status, severity, message, raw_data, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                            scan_id,
                            target_id,
                            choice(["info", "warning", "error"]),
                            choice(SEVERITIES),
                            f"Scan log entry for scan {scan_id}",
                            '{"type": "log", "source": "scanner"}',
                            start_time
                            + timedelta(minutes=uniform(0, duration_minutes)),
                        )

                print(f"  Scan {scan_id} for target {target_id}: {status}")

        print("\nDatabase seeding completed successfully!")
        print(f"  - 1 admin user ({admin_id})")
        print(f"  - {len(target_ids)} targets")
        print(f"  - Multiple scans with vulnerabilities and logs")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
