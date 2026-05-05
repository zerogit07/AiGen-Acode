import json
from pathlib import Path

FILE_SETTINGS = Path("settings.json")

def _baca_semua():
    if not FILE_SETTINGS.exists():
        return {}
    with open(FILE_SETTINGS, "r") as f:
        return json.load(f)

def _simpan_semua(data):
    with open(FILE_SETTINGS, "w") as f:
        json.dump(data, f, indent=2)

# --- GAMBAR ---
def ambil_gambar(nama):
    semua = _baca_semua()
    return semua.get(nama, None)

def simpan_gambar(nama, url):
    semua = _baca_semua()
    semua[nama] = url
    _simpan_semua(semua)

# --- DESKRIPSI PAKET ---
def ambil_deskripsi_paket(paket):
    """Baca deskripsi paket dari settings.json (harga / durasi / kuota)."""
    semua = _baca_semua()
    return semua.get(f"paket_{paket}", f"Paket {paket} - Deskripsi belum diatur.")

def simpan_deskripsi_paket(paket, teks):
    """Simpan deskripsi paket ke settings.json."""
    semua = _baca_semua()
    semua[f"paket_{paket}"] = teks
    _simpan_semua(semua)

# --- DATA MEMBER SEMENTARA ---
def set_member(user_id, paket):
    """Simpan data member ke settings.json (sementara)."""
    semua = _baca_semua()
    semua.setdefault("members", {})
    semua["members"][str(user_id)] = paket
    _simpan_semua(semua)

def get_member(user_id):
    """Ambil paket member dari settings.json."""
    semua = _baca_semua()
    return semua.get("members", {}).get(str(user_id), None)

# --- DESKRIPSI ---
def ambil_deskripsi(kunci):
    """Ambil teks deskripsi berdasarkan kunci."""
    semua = _baca_semua()
    return semua.get(f"deskripsi_{kunci}", "")

def simpan_deskripsi(kunci, teks):
    """Simpan teks deskripsi ke settings.json."""
    semua = _baca_semua()
    semua[f"deskripsi_{kunci}"] = teks
    _simpan_semua(semua)