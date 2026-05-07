import asyncio
import random
import time
from typing import Optional, Dict, List
from app.database.db import (
    get_all_proxies, get_all_fingerprints, get_api_keys
)

class ResourceManager:
    """
    Singleton yang mengelola Tripel Variabel.
    """
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self):
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            # Muat resource dari DB
            self.proxies: List[Dict] = []
            self.fingerprints: List[Dict] = []
            self.api_keys: List[str] = []
            await self._sync_db()

            # State internal
            self._rr_index = 0
            self._cooldowns: Dict[str, float] = {}
            self._locks: Dict[str, bool] = {}
            self._initialized = True

    async def _sync_db(self):
        """Sinkronisasi ulang dari database."""
        proxies = await get_all_proxies()
        self.proxies = [dict(p) for p in proxies if p.get("is_active")]
        fingerprints = await get_all_fingerprints()
        self.fingerprints = [dict(f) for f in fingerprints if f.get("is_active")]
        keys = await get_api_keys(active_only=True)
        self.api_keys = [k["key"] for k in keys]
        # Acak daftar untuk round robin
        random.shuffle(self.proxies)
        random.shuffle(self.fingerprints)

    async def get_next_available_set(self) -> Optional[Dict]:
        """
        Mengembalikan satu set Tripel Variabel yang tersedia.
        """
        await self.initialize()
        now = time.time()

        # Coba dapatkan kombinasi yang valid
        attempts = 0
        max_attempts = len(self.proxies) * len(self.fingerprints)
        while attempts < max_attempts:
            if not self.proxies or not self.fingerprints or not self.api_keys:
                return None

            proxy = self.proxies[self._rr_index % len(self.proxies)]
            fingerprint = self.fingerprints[self._rr_index % len(self.fingerprints)]
            api_key = random.choice(self.api_keys)
            self._rr_index += 1

            # Cek lock dan cooldown
            proxy_id = proxy["id"]
            fp_id = fingerprint["id"]
            if self._is_locked(proxy_id) or self._is_locked(fp_id):
                attempts += 1
                continue
            if self._is_cooldown(proxy_id, now) or self._is_cooldown(fp_id, now):
                attempts += 1
                continue

            # Kunci resource
            self._lock_resource(proxy_id)
            self._lock_resource(fp_id)

            return {
                "api_key": api_key,
                "proxy": proxy,
                "fingerprint": fingerprint,
            }

        return None  # Tidak ada yang tersedia

    async def release_set(self, set_data: Dict, failed: bool = False):
        """
        Lepaskan kunci set. Jika gagal, masukkan ke cooldown.
        """
        await self.initialize()
        proxy_id = set_data["proxy"]["id"]
        fp_id = set_data["fingerprint"]["id"]
        self._unlock_resource(proxy_id)
        self._unlock_resource(fp_id)
        if failed:
            cooldown_time = time.time() + 30 * 60  # 30 menit
            self._cooldowns[proxy_id] = cooldown_time
            self._cooldowns[fp_id] = cooldown_time

    async def sync_loop(self, interval: int = 600):
        """Loop latar belakang untuk sinkronisasi database."""
        while True:
            await asyncio.sleep(interval)
            try:
                await self._sync_db()
            except Exception as e:
                print(f"Sync error: {e}")

    def _lock_resource(self, resource_id):
        self._locks[resource_id] = True

    def _unlock_resource(self, resource_id):
        self._locks.pop(resource_id, None)

    def _is_locked(self, resource_id) -> bool:
        return self._locks.get(resource_id, False)

    def _is_cooldown(self, resource_id, now: float) -> bool:
        cooldown_until = self._cooldowns.get(resource_id)
        if cooldown_until and now < cooldown_until:
            return True
        if cooldown_until and now >= cooldown_until:
            del self._cooldowns[resource_id]
        return False