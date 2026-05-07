# app/services/backend_models/base.py

class BaseModel:
    """
    Cetakan dasar untuk semua model AI.
    Setiap model turunan WAJIB mengimplementasikan metode-metode di bawah.
    """

    # ============================================================
    # POST
    # ============================================================
    POST_URL: str = ""  # Diisi oleh model turunan, contoh: "https://api.magnific.com/v1/ai/text-to-video/veo-3-1"

    @staticmethod
    def build_payload(**kwargs) -> dict:
        """
        Merakit body JSON yang akan dikirim ke API.
        Setiap model punya parameter berbeda, jadi ini WAJIB ditimpa (override).
        """
        raise NotImplementedError("build_payload() harus diimplementasikan oleh model turunan.")

    @staticmethod
    def build_headers(api_key: str) -> dict:
        """
        Merakit header HTTP, termasuk API Key.
        Sebagian besar model di Magnific pakai format yang sama,
        jadi kita bisa sediakan default yang bisa dipakai langsung.
        """
        return {
            "x-magnific-api-key": api_key,
            "Content-Type": "application/json"
        }

    # ============================================================
    # GET (Polling)
    # ============================================================
    POLLING_URL: str = ""  # Template URL dengan placeholder {task_id}

    @classmethod
    def get_polling_url(cls, task_id: str) -> str:
        """
        Mengembalikan URL lengkap untuk mengecek status task.
        Default-nya menggunakan .format(task_id=...), sudah cocok untuk Magnific.
        """
        if not cls.POLLING_URL:
            raise NotImplementedError("POLLING_URL harus diisi oleh model turunan.")
        return cls.POLLING_URL.format(task_id=task_id)

    @staticmethod
    def parse_result(data: dict) -> dict:
        """
        Membaca response JSON dari polling dan mengembalikan data terstruktur:
        {
            "status": "COMPLETED" | "FAILED" | "IN_PROGRESS" | "CREATED",
            "videos": [...]  # hanya ada jika status COMPLETED
        }
        Default-nya mengikuti format standar Magnific.
        """
        status = data["data"]["status"]
        videos = data["data"].get("generated", [])
        return {"status": status, "videos": videos}