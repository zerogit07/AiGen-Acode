import json
from pathlib import Path

FILE_SETTINGS = Path("settings.json")

def _baca_semua():
    """Baca semua settings dari file JSON."""
    if not FILE_SETTINGS.exists():
        return {}
    with open(FILE_SETTINGS, "r") as f:
        return json.load(f)

def _simpan_semua(data):
    """Simpan semua settings ke file JSON."""
    with open(FILE_SETTINGS, "w") as f:
        json.dump(data, f, indent=2)

def ambil_gambar(nama):
    """Ambil URL gambar berdasarkan nama kunci."""
    semua = _baca_semua()
    return semua.get(nama, None)

def simpan_gambar(nama, url):
    """Simpan URL gambar ke settings."""
    semua = _baca_semua()
    semua[nama] = url
    _simpan_semua(semua)