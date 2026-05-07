A. Petunjuk Pemakaian
    1. Instal Python
    2. Clone Repository
    3. instal venv
    4. instal dependencies
    5. env
    6. jalankan 

B. Struktur Folder
AiGen-Studio/
├── source/
│   ├── handlers/         # Frontend handler (admin & model)
│   │   ├── frontend_admin/   # Handler panel admin
│   │   └── frontend_models/  # Handler models
│   ├── services/         # Backend logic (JobRunner, JobManager, dll.)
│   │   └── backend_models/   # Spesifikasi endpoint models
│   ├── keyboards/        # Inline keyboard builder
│   ├── database/         # SQLite helpers & database file (aigen.db)
│   ├── states/           # FSM states
│   └── utils/            # Fungsi pendukung (konversi gambar, dll.)
├── bot.py                # Entry point
├── config.py             # Konfigurasi dari .env
├── requirements.txt      # Daftar dependencies
├── README.md             # Dokumentasi ini
└── .env.example          # (opsional) contoh environment