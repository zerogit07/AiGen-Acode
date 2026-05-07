AiGen-Studio

AiGen-Studio adalah project berbasis Python untuk menjalankan sistem AI generation dengan struktur modular yang memisahkan frontend handler, backend services, database, dan utilities agar lebih mudah dikembangkan serta di-maintain.


---

A. Petunjuk Pemakaian

1. Install Python

Pastikan Python versi 3.10+ sudah terinstall.

Cek versi Python:

python --version

atau

python3 --version

Download Python resmi:

Python Official Website


---

2. Clone Repository

git clone https://github.com/username/AiGen-Studio.git

Masuk ke folder project:

cd AiGen-Studio


---

3. Install Virtual Environment (venv)

Windows

python -m venv venv

Aktifkan venv:

venv\Scripts\activate

Linux / macOS

python3 -m venv venv

Aktifkan venv:

source venv/bin/activate


---

4. Install Dependencies

pip install -r requirements.txt


---

5. Setup Environment

Buat file .env:

cp .env.example .env

Jika menggunakan Windows:

copy .env.example .env

Isi konfigurasi pada file .env sesuai kebutuhan:

BOT_TOKEN=your_bot_token
ADMIN_ID=your_telegram_id
DATABASE_URL=aigen.db

---

6. Jalankan Project

python bot.py

atau

python3 bot.py


---

B. Struktur Folder

AiGen-Studio/
├── source/
│   ├── handlers/                 # Frontend handler (admin & model)
│   │   ├── frontend_admin/       # Handler panel admin
│   │   └── frontend_models/      # Handler models
│   │
│   ├── services/                 # Backend logic
│   │   └── backend_models/       # Spesifikasi endpoint models
│   │
│   ├── keyboards/                # Inline keyboard builder
│   ├── database/                 # SQLite helpers & database file
│   ├── states/                   # FSM states
│   └── utils/                    # Helper & utility functions
│
├── bot.py                        # Entry point aplikasi
├── config.py                     # Konfigurasi dari .env
├── requirements.txt              # Daftar dependencies
├── README.md                     # Dokumentasi project
└── .env.example                  # Contoh environment

