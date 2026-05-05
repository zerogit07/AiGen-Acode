import aiosqlite

DB_PATH = "aigen.db"

async def init_db():
    """Membuat semua tabel jika belum ada."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        # Tabel members
        await db.execute("""
            CREATE TABLE IF NOT EXISTS members (
                user_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'non_member',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expired TEXT
            )
        """)

        # Tabel non_members
        await db.execute("""
            CREATE TABLE IF NOT EXISTS non_members (
                user_id INTEGER PRIMARY KEY,
                username TEXT
            )
        """)

        # Tabel limits
        await db.execute("""
            CREATE TABLE IF NOT EXISTS limits (
                paket TEXT PRIMARY KEY,
                process_limit INTEGER NOT NULL DEFAULT 5,
                daily_quota INTEGER NOT NULL DEFAULT 10
            )
        """)
        await db.execute("""
            INSERT OR IGNORE INTO limits (paket, process_limit, daily_quota) VALUES
                ('Lite', 5, 10),
                ('Pro', 10, 25),
                ('Ultra', 15, 50)
        """)

        # Tabel api_keys
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                name TEXT PRIMARY KEY,
                key TEXT NOT NULL
            )
        """)

        # Tabel proxies
        await db.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL
            )
        """)

        # Tabel pages
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                page_name TEXT PRIMARY KEY,
                gambar TEXT,
                deskripsi TEXT,
                harga INTEGER
            )
        """)

        await db.commit()
    finally:
        await db.close()


async def migrate_json_to_db():
    """Migrasi data dari settings.json ke database (dijalankan sekali)."""
    import json
    from pathlib import Path

    settings_path = Path("settings.json")
    if not settings_path.exists():
        return

    with open(settings_path, "r") as f:
        data = json.load(f)

    db = await aiosqlite.connect(DB_PATH)
    try:
        # Migrasi members
        members = data.get("members", {})
        for uid, paket in members.items():
            await db.execute(
                "INSERT OR REPLACE INTO members (user_id, status) VALUES (?, ?)",
                (int(uid), paket)
            )

        # Migrasi non_members
        nonmembers = data.get("nonmember", [])
        for uid in nonmembers:
            await db.execute(
                "INSERT OR IGNORE INTO non_members (user_id) VALUES (?)",
                (uid,)
            )

        # Migrasi pages
        for key in ["banner", "lite", "pro", "ultra", "start_image", "qris"]:
            gambar = data.get(key)
            deskripsi = data.get(f"deskripsi_{key}")
            harga = data.get(f"harga_{key}")

            if gambar or deskripsi or harga:
                await db.execute(
                    "INSERT OR REPLACE INTO pages (page_name, gambar, deskripsi, harga) VALUES (?, ?, ?, ?)",
                    (key, gambar, deskripsi, harga)
                )

        await db.commit()
    finally:
        await db.close()