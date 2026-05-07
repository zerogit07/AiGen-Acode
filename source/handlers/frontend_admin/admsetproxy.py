from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.states.admin_proxy import AdminProxyState
from source.database.db import (
    get_all_proxies, add_proxy, delete_proxy, toggle_proxy, reset_proxies
)
from config import ADMIN_ID

router = Router()

# ========== MENU UTAMA SETTING PROXY ==========
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

# ========== MANAJEMEN PROXY (DAFTAR) ==========
@router.callback_query(F.data == "proxy_manage")
async def proxy_manage_list(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxies = await get_all_proxies()
    lines = ["🌐 <b>Daftar Proxy</b>\n"]
    if not proxies:
        lines.append("(Belum ada proxy)")

    builder = InlineKeyboardBuilder()
    for p in proxies:
        status = "🟢" if p[5] else "🔴"
        # p[1]=username, p[3]=host, p[4]=port
        lines.append(f"{status} {p[1][:25]}... @ {p[3]}:{p[4]}")

        builder.button(text="Detail", callback_data=f"proxy_detail_{p[0]}")
        builder.button(
            text="Nonaktifkan" if p[5] else "Aktifkan",
            callback_data=f"proxy_toggle_{p[0]}"
        )
        builder.button(text="🗑️ Hapus", callback_data=f"proxy_delete_{p[0]}")

    builder.button(text="🔙 Kembali".center(25), callback_data="admin_set_proxy")
    builder.adjust(3)  # 3 tombol aksi per proxy, lalu tombol kembali

    await callback.message.edit_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()

# ========== DETAIL PROXY ==========
@router.callback_query(F.data.startswith("proxy_detail_"))
async def proxy_detail(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    proxies = await get_all_proxies()
    target = next((p for p in proxies if p[0] == proxy_id), None)
    if not target:
        await callback.answer("Proxy tidak ditemukan.", show_alert=True)
        return

    is_active = "🟢 Aktif" if target[5] else "🔴 Nonaktif"
    text = (
        f"🌐 <b>Detail Proxy</b>\n\n"
        f"ID: {target[0]}\n"
        f"Username: <code>{target[1]}</code>\n"
        f"Password: <code>{target[2]}</code>\n"
        f"Host: <code>{target[3]}</code>\n"
        f"Port: <code>{target[4]}</code>\n"
        f"Status: {is_active}\n\n"
        f"⚠️ <i>Ini rahasia. Jangan bagikan ke siapa pun.</i>"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Daftar".center(25), callback_data="proxy_manage")

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

# ========== TOGGLE AKTIF/NONAKTIF ==========
@router.callback_query(F.data.startswith("proxy_toggle_"))
async def proxy_toggle(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    pid, new_state = await toggle_proxy(proxy_id)
    await callback.answer(f"Proxy {pid} {'aktif' if new_state else 'nonaktif'}.", show_alert=True)
    await proxy_manage_list(callback)

# ========== HAPUS PROXY ==========
@router.callback_query(F.data.startswith("proxy_delete_"))
async def proxy_delete(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    proxy_id = int(callback.data.split("_")[2])
    await delete_proxy(proxy_id)
    await callback.answer("Proxy dihapus.", show_alert=True)
    await proxy_manage_list(callback)

# ========== TAMBAH PROXY (FSM) ==========
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
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_proxy"}]]
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
                # Format: USER:PASS@HOST:PORT
                creds, hostport = line.split("@")
                username, password = creds.split(":", 1)
                host, port = hostport.split(":")
            else:
                # Format: USER:PASS:HOST:PORT
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
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali ke Setting Proxy", "callback_data": "admin_set_proxy"}]]
        ).as_markup()
    )

# ========== RESET PROXY (FSM) ==========
@router.callback_query(F.data == "proxy_reset")
async def proxy_reset_prompt(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminProxyState.reset_proxy)
    await callback.message.edit_text(
        "<b>⚠️ Reset Proxy</b>\n\n"
        "Ini akan <b>menghapus semua proxy</b> yang ada.\n"
        "Kirim daftar proxy baru (satu atau lebih):\n\n"
        "<code>USERNAME:PASSWORD@HOST:PORT</code>\n"
        "atau\n"
        "<code>USERNAME:PASSWORD:HOST:PORT</code>\n\n"
        "Pisahkan dengan enter.\n"
        "Ketik /cancel untuk batal.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_proxy"}]]
        ).as_markup()
    )
    await callback.answer()

@router.message(AdminProxyState.reset_proxy)
async def proxy_reset_process(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    lines = message.text.strip().split("\n")
    new_list = []

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
                    continue
                username, password, host, port = parts
            new_list.append((username, password, host, int(port)))
        except Exception:
            pass

    if not new_list:
        await message.answer(
            "Tidak ada proxy valid untuk di-reset.",
            reply_markup=InlineKeyboardBuilder(
                buttons=[[{"text": "🔙 Kembali", "callback_data": "admin_set_proxy"}]]
            ).as_markup()
        )
        return

    count = await reset_proxies(new_list)
    await state.clear()
    await message.answer(
        f"🔄 {count} proxy baru berhasil dimasukkan (data lama terhapus).",
        reply_markup=InlineKeyboardBuilder(
            buttons=[[{"text": "🔙 Kembali ke Setting Proxy", "callback_data": "admin_set_proxy"}]]
        ).as_markup()
    )

# ========== CANCEL ==========
@router.message(F.command == "cancel")
async def proxy_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.")