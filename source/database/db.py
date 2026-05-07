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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
            )
        """)


        # Tabel proxies
        await db.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            last_used TEXT
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
        # Tabel models
        await db.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                callback_data TEXT NOT NULL UNIQUE,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        # Isi default model jika masih kosong
        cursor = await db.execute("SELECT COUNT(*) FROM models")
        count = (await cursor.fetchone())[0]
        if count == 0:
            default_models = [
                ("🎬 Kling V3", "model_kling_v3"),
                ("🚀 Kling V3 Motion", "model_kling_v3_motion"),
                ("🌀 Kling V3 Omni", "model_kling_v3_omni"),
                ("⚡ Kling 2.6 Pro", "model_kling_26_pro"),
                ("💨 Kling 2.6 Motion", "model_kling_26_motion"),
                ("🔥 Kling 2.5 Turbo", "model_kling_25_turbo"),
                ("🎯 Kling 2.1", "model_kling_21"),
                ("🧠 Kling O1", "model_kling_o1"),
                ("🌌 Veo 3.1", "model_veo_31"),
                ("🍌 Nano Banana", "model_nano_banana"),
            ]
            for idx, (name, cb) in enumerate(default_models, 1):
                await db.execute(
                    "INSERT INTO models (name, callback_data, is_active, sort_order) VALUES (?, ?, 1, ?)",
                    (name, cb, idx)
                )
                
                # Tabel fingerprints
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS fingerprints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ja3_string TEXT,
                   user_agent TEXT,
                  is_active INTEGER DEFAULT 1
                  )
                """)
                # Isi default jika kosong
        cursor = await db.execute("SELECT COUNT(*) FROM fingerprints")
        count = (await cursor.fetchone())[0]
        if count == 0:
            default_fingerprints = [
                ("Chrome 127 Windows", "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"),
                ("Firefox 129 Windows", "4865-4867-4866-49195-49199-52393-52392-49196-49200-49171-49172-156-157-47-53", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"),
                ("Chrome 127 Mac", "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"),
            ]
            for name, ja3, ua in default_fingerprints:
                await db.execute(
                    "INSERT INTO fingerprints (name, ja3_string, user_agent) VALUES (?, ?, ?)",
                    (name, ja3, ua)
                )
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
        

async def get_limit(paket: str):
    """Ambil limit paket. Kembalikan dict {'process_limit': int, 'daily_quota': int}."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute(
            "SELECT process_limit, daily_quota FROM limits WHERE paket = ?",
            (paket,)
        )
        row = await cursor.fetchone()
        if row:
            return {"process_limit": row[0], "daily_quota": row[1]}
        return None
    finally:
        await db.close()

async def set_limit(paket: str, process_limit: int, daily_quota: int):
    """Update limit untuk suatu paket."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "UPDATE limits SET process_limit = ?, daily_quota = ? WHERE paket = ?",
            (process_limit, daily_quota, paket)
        )
        await db.commit()
    finally:
        await db.close()

async def import_csv_to_table(table_name: str, headers: list, rows: list):
    """Mengimpor data CSV ke tabel. Menghapus data lama terlebih dahulu."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(f"DELETE FROM {table_name}")
        placeholders = ",".join(["?" for _ in headers])
        sql = f"INSERT INTO {table_name} ({','.join(headers)}) VALUES ({placeholders})"
        await db.executemany(sql, rows)
        await db.commit()
        return len(rows)
    finally:
        await db.close()
        

async def export_table(table_name: str):
    """Mengembalikan tuple (headers, rows) dari sebuah tabel."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute(f"SELECT * FROM {table_name}")
        rows = await cursor.fetchall()
        cursor_desc = await db.execute(f"PRAGMA table_info({table_name})")
        columns = await cursor_desc.fetchall()
        headers = [col[1] for col in columns]
        return headers, rows
    finally:
        await db.close()
        

async def get_all_models(active_only: bool = False):
    db = await aiosqlite.connect(DB_PATH)
    try:
        if active_only:
            cursor = await db.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY sort_order ASC")
        else:
            cursor = await db.execute("SELECT * FROM models ORDER BY sort_order ASC")
        return await cursor.fetchall()
    finally:
        await db.close()

async def swap_model_order(id1: int, id2: int):
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute("SELECT sort_order FROM models WHERE id = ?", (id1,))
        row1 = await cursor.fetchone()
        cursor = await db.execute("SELECT sort_order FROM models WHERE id = ?", (id2,))
        row2 = await cursor.fetchone()
        if not row1 or not row2:
            return False
        await db.execute("UPDATE models SET sort_order = ? WHERE id = ?", (row2[0], id1))
        await db.execute("UPDATE models SET sort_order = ? WHERE id = ?", (row1[0], id2))
        await db.commit()
        return True
    finally:
        await db.close()

async def toggle_model_active(model_id: int):
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "UPDATE models SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (model_id,)
        )
        await db.commit()
        cursor = await db.execute("SELECT name, is_active FROM models WHERE id = ?", (model_id,))
        row = await cursor.fetchone()
        return row if row else (None, None)
    finally:
        await db.close()
        
# ====================================================================
# API KEY
# ====================================================================
async def get_api_keys():
    """Mengembalikan list dictionary semua API key."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute("SELECT id, key, is_active FROM api_keys ORDER BY id")
        rows = await cursor.fetchall()
        return [
            {"id": row[0], "key": row[1], "is_active": row[2]}
            for row in rows
        ]
    finally:
        await db.close()

async def add_api_keys_bulk(keys: list):
    """Tambah banyak API key sekaligus."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        for key in keys:
            await db.execute(
                "INSERT INTO api_keys (key, is_active) VALUES (?, 1)",
                (key,)
            )
        await db.commit()
        return len(keys)
    finally:
        await db.close()

async def delete_api_key(key_id: int):
    """Hapus satu API key."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("DELETE FROM api_keys WHERE id = ?", (key_id,))
        await db.commit()
    finally:
        await db.close()

async def toggle_api_key(key_id: int):
    """Toggle is_active API key, kembalikan (id, is_active)."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "UPDATE api_keys SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (key_id,)
        )
        await db.commit()
        cursor = await db.execute("SELECT id, is_active FROM api_keys WHERE id = ?", (key_id,))
        row = await cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally:
        await db.close()

async def reset_api_keys():
    """Hapus semua API key."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("DELETE FROM api_keys")
        await db.commit()
    finally:
        await db.close()

# ====================================================================
# PROXY
# ====================================================================
async def get_all_proxies():
    """Mengembalikan list dictionary semua proxy."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute(
            "SELECT id, username, password, host, port, is_active, last_used FROM proxies ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "username": row[1],
                "password": row[2],
                "host": row[3],
                "port": row[4],
                "is_active": row[5],
                "last_used": row[6],
            }
            for row in rows
        ]
    finally:
        await db.close()

async def add_proxy(username: str, password: str, host: str, port: int):
    """Tambahkan satu proxy."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "INSERT INTO proxies (username, password, host, port) VALUES (?, ?, ?, ?)",
            (username, password, host, port)
        )
        await db.commit()
    finally:
        await db.close()

async def delete_proxy(proxy_id: int):
    """Hapus proxy."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
        await db.commit()
    finally:
        await db.close()

async def toggle_proxy(proxy_id: int):
    """Toggle is_active proxy, kembalikan (id, is_active)."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "UPDATE proxies SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (proxy_id,)
        )
        await db.commit()
        cursor = await db.execute("SELECT id, is_active FROM proxies WHERE id = ?", (proxy_id,))
        row = await cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)
    finally:
        await db.close()

async def reset_proxies():
    """Hapus semua proxy."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute("DELETE FROM proxies")
        await db.commit()
    finally:
        await db.close()

# ====================================================================
# FINGERPRINT
# ====================================================================
async def get_all_fingerprints():
    """Mengembalikan list dictionary fingerprint aktif."""
    db = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await db.execute(
            "SELECT id, name, ja3_string, user_agent, is_active FROM fingerprints WHERE is_active = 1 ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "ja3_string": row[2],
                "user_agent": row[3],
                "is_active": row[4],
            }
            for row in rows
        ]
    finally:
        await db.close()