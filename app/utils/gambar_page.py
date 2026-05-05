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

# --- HARGA PAKET ---
def ambil_harga(paket):
    """Ambil harga dasar paket (integer). Kembalikan None jika belum diatur."""
    semua = _baca_semua()
    return semua.get(f"harga_{paket}", None)

def simpan_harga(paket, jumlah):
    """Simpan harga dasar paket (integer)."""
    semua = _baca_semua()
    semua[f"harga_{paket}"] = jumlah
    _simpan_semua(semua)
    
# --- NON‑MEMBER ---
def catat_nonmember(user_id):
    semua = _baca_semua()
    semua.setdefault("nonmember", [])
    if user_id not in semua["nonmember"]:
        semua["nonmember"].append(user_id)
        _simpan_semua(semua)

def ambil_semua_nonmember():
    semua = _baca_semua()
    return semua.get("nonmember", [])

def ambil_semua_member():
    semua = _baca_semua()
    return semua.get("members", {})

#----member setting----   
def hapus_member(user_id):
    semua = _baca_semua()
    members = semua.get("members", {})
    members.pop(str(user_id), None)
    semua["members"] = members
    _simpan_semua(semua)

def semua_member_urut():
    semua = _baca_semua()
    members = semua.get("members", {})
    # Urutkan berdasarkan user_id (integer)
    return dict(sorted(members.items(), key=lambda x: int(x[0])))