# app/services/job_runner.py

import asyncio
import random
import time
import uuid
from typing import Dict

import aiohttp
from aiogram import Bot

from app.services.resource_manager import ResourceManager


class JobRunner:
    """
    Pelaksana satu job video secara end‑to‑end:
    POST → retry (jika gagal) → polling → notifikasi user.
    """

    def __init__(
        self,
        job_data: Dict,
        tripel_set: Dict,
        resource_mgr: ResourceManager,
        on_done_callback,
        bot: Bot,
    ):
        self.id = str(uuid.uuid4())
        self.job_data = job_data
        self.tripel = tripel_set          # api_key, proxy, fingerprint
        self.resource_mgr = resource_mgr
        self.on_done = on_done_callback
        self.bot = bot

        # Model backend dan parameter dari user
        self.model = job_data.get("model")
        self.params = job_data.get("params", {})
        self.user_id = job_data.get("user_id")

        # Konfigurasi retry & jeda
        self.max_retries = 5
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.post_jitter = lambda: abs(random.gauss(10, 3))
        self.polling_interval = lambda: abs(random.gauss(12.5, 2.5))

    # ============================================================
    # ALUR UTAMA
    # ============================================================
    async def run(self):
        """Jalankan seluruh alur: POST → Polling → Notifikasi → Cleanup."""
        session = await self._create_session()
        task_id = None
        try:
            # --- POST dengan retry ---
            for attempt in range(1, self.max_retries + 1):
                try:
                    task_id = await self._do_post(session)
                    break
                except Exception as e:
                    print(f"POST attempt {attempt} gagal: {e}")
                    if attempt < self.max_retries:
                        # Lepas set gagal, cooling down
                        await self.resource_mgr.release_set(
                            self.tripel, failed=True
                        )
                        await asyncio.sleep(self.post_jitter())

                        # Ambil set baru
                        self.tripel = await self.resource_mgr.get_next_available_set()
                        if not self.tripel:
                            print("Tidak ada resource tersedia setelah retry.")
                            break

                        # Buat sesi baru dengan set baru
                        await session.close()
                        session = await self._create_session()

            # --- Polling & notifikasi ---
            if task_id:
                result = await self._polling(session, task_id)
                await self._notify_user(result)
            else:
                await self._notify_user({
                    "status": "FAILED",
                    "message": "Gagal membuat video setelah beberapa percobaan.",
                })
        finally:
            if session:
                await session.close()
            if self.tripel:
                await self.resource_mgr.release_set(
                    self.tripel, failed=(task_id is None)
                )
            await self.on_done(self)

    # ============================================================
    # SESSION & HTTP CALLS
    # ============================================================
    async def _create_session(self) -> aiohttp.ClientSession:
        """Buat session aiohttp dengan proxy & header spoofing."""
        proxy_host = self.tripel["proxy"]["host"]
        proxy_port = self.tripel["proxy"]["port"]
        proxy_url = f"http://{proxy_host}:{proxy_port}" #noqa
        proxy_auth = aiohttp.BasicAuth( #noqa
            self.tripel["proxy"]["username"],
            self.tripel["proxy"]["password"],
        )

        headers = {
            "User-Agent": self.tripel["fingerprint"].get(
                "user_agent", "Mozilla/5.0"
            ),
        }

        connector = aiohttp.TCPConnector(ssl=False)
        return aiohttp.ClientSession(connector=connector, headers=headers)

    async def _do_post(self, session: aiohttp.ClientSession) -> str:
        """Kirim POST ke Magnific. Kembalikan task_id."""
        url = self.model.POST_URL
        payload = self.model.build_payload(**self.params)
        headers = self.model.build_headers(self.tripel["api_key"])

        proxy_host = self.tripel["proxy"]["host"]
        proxy_port = self.tripel["proxy"]["port"]
        proxy_url = f"http://{proxy_host}:{proxy_port}"
        proxy_auth = aiohttp.BasicAuth(
            self.tripel["proxy"]["username"],
            self.tripel["proxy"]["password"],
        )

        await asyncio.sleep(self.post_jitter())

        async with session.post(
            url,
            json=payload,
            headers=headers,
            proxy=proxy_url,
            proxy_auth=proxy_auth,
            timeout=self.timeout,
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["data"]["task_id"]
            else:
                body = await resp.text()
                raise Exception(f"HTTP {resp.status}: {body}")

    async def _polling(
        self, session: aiohttp.ClientSession, task_id: str
    ) -> Dict:
        """Polling status task sampai COMPLETED / FAILED / timeout."""
        url = self.model.get_polling_url(task_id)
        headers = self.model.build_headers(self.tripel["api_key"])

        proxy_host = self.tripel["proxy"]["host"]
        proxy_port = self.tripel["proxy"]["port"]
        proxy_url = f"http://{proxy_host}:{proxy_port}" 
        proxy_auth = aiohttp.BasicAuth(
            self.tripel["proxy"]["username"],
            self.tripel["proxy"]["password"],
        )

        max_duration = 30 * 60  # 30 menit
        start_time = time.time()

        while time.time() - start_time < max_duration:
            await asyncio.sleep(self.polling_interval())
            async with session.get(
                url,
                headers=headers,
                proxy=proxy_url,
                proxy_auth=proxy_auth,
                timeout=self.timeout,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    status = data["data"]["status"]
                    if status == "COMPLETED":
                        return {
                            "status": "COMPLETED",
                            "videos": data["data"].get("generated", []),
                        }
                    elif status == "FAILED":
                        return {
                            "status": "FAILED",
                            "message": "Proses oleh API gagal.",
                        }
                else:
                    print(f"Polling HTTP {resp.status}")

        return {"status": "FAILED", "message": "Polling melebihi waktu maksimal."}

    # ============================================================
    # NOTIFIKASI
    # ============================================================
    async def _notify_user(self, result: Dict):
        """Kirim notifikasi hasil ke user via Telegram."""
        if not self.bot:
            print(
                f"[WARN] Bot tidak tersedia. Tidak bisa kirim ke {self.user_id}"
            )
            return

        try:
            if result.get("status") == "COMPLETED":
                videos = result.get("videos", [])
                if videos:
                    await self.bot.send_message(
                        chat_id=self.user_id,
                        text=f"🎉 Video selesai!\n{videos[0]}",
                    )
                else:
                    await self.bot.send_message(
                        chat_id=self.user_id,
                        text="🎉 Video selesai, tapi link tidak tersedia.",
                    )
            else:
                message = result.get("message", "Gagal.")
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=f"❌ Maaf, video gagal dibuat.\n{message}",
                )
        except Exception as e:
            print(f"Gagal kirim notifikasi ke {self.user_id}: {e}")