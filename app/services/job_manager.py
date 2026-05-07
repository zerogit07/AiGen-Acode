# app/services/job_manager.py

import asyncio
from typing import Dict, List, Optional
from aiogram import Bot
from app.services.resource_manager import ResourceManager
from app.services.job_runner import JobRunner

class JobManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self, bot: Optional[Bot] = None):
        if self._initialized:
            # Perbarui bot jika dikirim ulang
            if bot: 
                self.bot = bot
            return
        async with self._lock:
            if self._initialized:
                return
            self.bot = bot                                          # ← Simpan Bot instance
            self.resource_mgr = ResourceManager()
            await self.resource_mgr.initialize()
            self.queue: List[Dict] = []
            self.active_jobs: Dict[str, JobRunner] = {}
            self.max_jobs = 10
            self._dispatcher_task = asyncio.create_task(self._dispatcher())
            self._initialized = True

    async def enqueue(self, job_data: Dict):
        await self.initialize()
        self.queue.append(job_data)
        print(f"Job enqueued. Queue size: {len(self.queue)}")

    async def _dispatcher(self):
        while True:
            await self.initialize()
            while len(self.active_jobs) < self.max_jobs and self.queue:
                job_data = self.queue.pop(0)
                tripel_set = await self.resource_mgr.get_next_available_set()
                if tripel_set is None:
                    self.queue.insert(0, job_data)
                    await asyncio.sleep(5)
                    continue

                # --- Kirim Bot instance ke JobRunner ---
                runner = JobRunner(job_data, tripel_set, self.resource_mgr, self._on_job_done, self.bot)
                asyncio.create_task(runner.run())
                self.active_jobs[runner.id] = runner
                print(f"Job started: {runner.id}. Active: {len(self.active_jobs)}")

            await asyncio.sleep(2)

    async def _on_job_done(self, runner: JobRunner):
        await self.initialize()
        self.active_jobs.pop(runner.id, None)
        print(f"Job finished: {runner.id}. Active: {len(self.active_jobs)}")