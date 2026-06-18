import asyncio

import asyncpg

DATABASE_URL = "postgresql://vapt:vapt-secret-password@localhost:5432/vapt"

TABLES = [
    "scan_logs",
    "vulnerabilities",
    "scans",
    "targets",
    "users",
    "alembic_version",
]

SEQUENCES = [
    "users_id_seq",
    "targets_id_seq",
    "scans_id_seq",
    "vulnerabilities_id_seq",
    "scan_logs_id_seq",
]


async def reset_database():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for table in TABLES:
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"Dropped table: {table}")

        for seq in SEQUENCES:
            await conn.execute(f"DROP SEQUENCE IF EXISTS {seq} CASCADE")
            print(f"Dropped sequence: {seq}")

        print("\nAll tables dropped. Running migrations...")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'user',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        )
        print("Created table: users")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS targets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                url TEXT NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'web',
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        )
        print("Created table: targets")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
                scan_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                duration_seconds INTEGER,
                parameters JSONB,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        )
        print("Created table: scans")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT,
                remediation TEXT,
                cvss_score DECIMAL(3,1),
                cve_id VARCHAR(50),
                discovered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                status VARCHAR(50) NOT NULL DEFAULT 'open',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        )
        print("Created table: vulnerabilities")

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
                target_id UUID NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
                status VARCHAR(50) NOT NULL,
                severity VARCHAR(20),
                message TEXT,
                raw_data JSONB,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """
        )
        print("Created table: scan_logs")

        await conn.execute(
            "SELECT create_hypertable('scan_logs', 'created_at', if_not_exists => TRUE)"
        )
        print("Converted scan_logs to hypertable")

        print("\nDatabase reset completed successfully!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(reset_database())
