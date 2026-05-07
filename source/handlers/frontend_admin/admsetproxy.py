from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.admin_proxy import AdminProxyState
from source.database.db import (
    get_all_proxies, add_proxy, delete_proxy,
    toggle_proxy, reset_proxies
)
from config import ADMIN_ID

router = Router()

PROXIES_PER_PAGE = 10

# ------------------------------------------------------------
# MENU UTAMA SETTING PROXY
# ------------------------------------------------------------
@router.callback_query(F.data == "admin_set_proxy")
async def admsetproxy_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Manajemen Proxy".center(25), callback_data="proxy_manage")
    builder.button(text="➕ Tambah Proxy".center(25), callback_data="proxy_add")
    builder.button(text="🔄 Reset Proxy".center(25), callback_data="proxy_reset")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>🌐 Setting Proxy</b>\nSilakan pilih menu:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# MANAJEMEN PROXY (DAFTAR) - Halaman pertama
# ------------------------------------------------------------
@router.callback_query(F.data == "proxy_manage")
async def proxy_manage_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    await show_proxy_page(callback, page=1)

# ------------------------------------------------------------
# NAVIGASI HALAMAN PROXY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("proxy_page_"))
async def proxy_page_handler(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return
    page = int(callback.data.split("_")[-1])
    await show_proxy_page(callback, page)

async def show_proxy_page(callback: types.CallbackQuery, page: int):
    proxies = await get_all_proxies()
    total_pages = max(1, (len(proxies) + PROXIES_PER_PAGE - 1) // PROXIES_PER_PAGE)
    start = (page - 1) * PROXIES_PER_PAGE
    end = start + PROXIES_PER_PAGE
    page_proxies = proxies[start:end]

    lines = [f"🌐 <b>Manajemen Proxy ({page}/{total_pages})</b>"]

    # Susun tombol secara manual
    keyboard_rows = []

    if not page_proxies:
        lines.append("(Belum ada proxy)")
    else:
        for p in page_proxies:
            proxy_id = p["id"]
            full_host_port = f"{p['host']}:{p['port']}"
            # Ambil maksimal 18 karakter dari belakang
            short_host = full_host_port[-18:] if len(full_host_port) > 18 else full_host_port
            is_active = p["is_active"]

            # Satu baris: 4 tombol
            row = [
                InlineKeyboardButton(text=short_host, callback_data=f"proxy_detail_{proxy_id}"),
                InlineKeyboardButton(text="🔍", callback_data=f"proxy_info_{proxy_id}"),
                InlineKeyboardButton(text="🟢" if is_active else "🔴", callback_data=f"proxy_toggle_{proxy_id}"),
                InlineKeyboardButton(text="🗑️", callback_data=f"proxy_delete_{proxy_id}"),
            ]
            keyboard_rows.append(row)

    # Baris navigasi
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅️ Sebelumnya", callback_data=f"proxy_page_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(text="➡️ Selanjutnya", callback_data=f"proxy_page_{page+1}"))
    if nav_row:
        keyboard_rows.append(nav_row)

    # Baris tombol Kembali
    back_row = [InlineKeyboardButton(text="🔙 Kembali", callback_data="admin_set_proxy")]
    keyboard_rows.append(back_row)

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=markup
    )
    await callback.answer()

# ------------------------------------------------------------
# DETAIL PROXY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("proxy_detail_"))
async def proxy_detail(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    proxies = await get_all_proxies()
    target = next((p for p in proxies if p["id"] == proxy_id), None)
    if not target:
        await callback.answer("Proxy tidak ditemukan.", show_alert=True)
        return

    is_active = "🟢 Aktif" if target["is_active"] else "🔴 Nonaktif"
    text = (
        f"🌐 <b>Detail Proxy</b>\n\n"
        f"ID: {target['id']}\n"
        f"Username: <code>{target['username']}</code>\n"
        f"Password: <code>{target['password']}</code>\n"
        f"Host: <code>{target['host']}</code>\n"
        f"Port: <code>{target['port']}</code>\n"
        f"Status: {is_active}\n\n"
        f"⚠️ <i>Ini rahasia. Jangan bagikan ke siapa pun.</i>"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Manajemen", callback_data="proxy_manage"
        ).as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# TOGGLE AKTIF/NONAKTIF
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("proxy_toggle_"))
async def proxy_toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    pid, new_state = await toggle_proxy(proxy_id)
    await callback.answer(
        f"Proxy {pid} {'aktif' if new_state else 'nonaktif'}.",
        show_alert=True
    )
    await show_proxy_page(callback, page=1)

# ------------------------------------------------------------
# HAPUS PROXY
# ------------------------------------------------------------
@router.callback_query(F.data.startswith("proxy_delete_"))
async def proxy_delete(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    await delete_proxy(proxy_id)
    await callback.answer("Proxy dihapus.", show_alert=True)
    await show_proxy_page(callback, page=1)

# ------------------------------------------------------------
# TAMBAH PROXY (FSM)
# ------------------------------------------------------------
@router.callback_query(F.data == "proxy_add")
async def proxy_add_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminProxyState.tambah_proxy)
    await callback.message.edit_text(
        "<b>Tambah Proxy</b>\n\n"
        "Kirim kredensial proxy (satu atau lebih):\n\n"
        "<code>USERNAME:PASSWORD@HOST:PORT</code>\n"
        "atau\n"
        "<code>USERNAME:PASSWORD:HOST:PORT</code>\n\n"
        "Pisahkan dengan enter jika lebih dari satu.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali", callback_data="admin_set_proxy"
        ).as_markup()
    )
    await callback.answer()

@router.message(AdminProxyState.tambah_proxy)
async def proxy_add_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lines = message.text.strip().split("\n")
    added = 0
    errors = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            if "@" in line:
                creds, hostport = line.split("@")
                username, password = creds.split(":", 1)
                host, port = hostport.split(":")
            else:
                parts = line.split(":")
                if len(parts) != 4:
                    errors.append(f"Format salah: {line}")
                    continue
                username, password, host, port = parts
            await add_proxy(username, password, host, int(port))
            added += 1
        except Exception:
            errors.append(f"Gagal parse: {line}")

    msg = f"✅ {added} proxy berhasil ditambahkan."
    if errors:
        msg += f"\n❌ {len(errors)} gagal."

    await state.clear()
    await message.answer(
        msg,
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Setting Proxy", callback_data="admin_set_proxy"
        ).as_markup()
    )

# ------------------------------------------------------------
# RESET PROXY (KONFIRMASI YES / NO)
# ------------------------------------------------------------
@router.callback_query(F.data == "proxy_reset")
async def proxy_reset_prompt(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ya", callback_data="proxy_reset_confirm")
    builder.button(text="❌ Tidak", callback_data="admin_set_proxy")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>⚠️ Anda yakin ingin mereset semua proxy?</b>\n"
        "Semua proxy yang tersimpan akan dihapus permanen.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "proxy_reset_confirm")
async def proxy_reset_confirm(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await reset_proxies()
    await callback.message.edit_text(
        "🔄 Semua proxy berhasil dihapus.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Kembali ke Setting Proxy", callback_data="admin_set_proxy"
        ).as_markup()
    )
    await callback.answer()

# ------------------------------------------------------------
# CANCEL
# ------------------------------------------------------------
@router.message(F.command == "cancel")
async def proxy_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.")