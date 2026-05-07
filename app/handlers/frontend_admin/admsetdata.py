import csv
import io
from aiogram import Router, F, types, Bot
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.db import export_table, import_csv_to_table
from app.states.admin_data import AdminDataState
from config import ADMIN_ID

router = Router()

TABLES = {
    "Members": "members",
    "Non Members": "non_members",
    "Limits": "limits",
    "Pages": "pages",
    "API Keys": "api_keys",
    "Proxies": "proxies",
}

def back_to_data():
    return InlineKeyboardBuilder(
        buttons=[
            [{"text": "🔙 Kembali ke Setting Data", "callback_data": "admin_set_data"}]
        ]
    ).as_markup()


# ================= MENU UTAMA =================
@router.callback_query(F.data == "admin_set_data")
async def admsetdata_menu(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Export CSV".center(25), callback_data="data_export")
    builder.button(text="📥 Import CSV".center(25), callback_data="data_import")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_panel")
    builder.adjust(2)

    await callback.message.edit_text(
        "<b>🗄️ Setting Data</b>\nPilih operasi:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ================= EXPORT =================
@router.callback_query(F.data == "data_export")
async def data_export_pilih_tabel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for label, name in TABLES.items():
        builder.button(text=label.center(25), callback_data=f"export_{name}")
    builder.button(text="📦 Semua Tabel".center(25), callback_data="export_all")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_set_data")
    builder.adjust(1)

    await callback.message.edit_text(
        "<b>Pilih tabel yang akan diexport:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("export_"))
async def data_do_export(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    target = callback.data.replace("export_", "")

    if target == "all":
        await callback.answer("Fitur export semua tabel akan datang.", show_alert=True)
        return

    headers, rows = await export_table(target)
    if not rows:
        await callback.answer("Tabel kosong.", show_alert=True)
        return

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    file = BufferedInputFile(
        output.getvalue().encode("utf-8"),
        filename=f"{target}.csv"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_set_data")
    builder.adjust(1)

    await callback.message.answer_document(
        document=file,
        caption=f"✅ Export tabel `{target}` berhasil.",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ================= IMPORT =================
@router.callback_query(F.data == "data_import")
async def data_import_pilih_tabel(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    await state.set_state(AdminDataState.pilih_tabel)

    builder = InlineKeyboardBuilder()
    for label, name in TABLES.items():
        builder.button(text=label.center(25), callback_data=f"import_{name}")
    builder.button(text="🔙 Kembali".center(25), callback_data="admin_set_data")
    builder.adjust(1)

    await callback.message.edit_text(
        "<b>Pilih tabel tujuan impor:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(AdminDataState.pilih_tabel, F.data.startswith("import_"))
async def data_import_upload(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    table_name = callback.data.replace("import_", "")
    await state.update_data(table_name=table_name)
    await state.set_state(AdminDataState.upload_file)

    await callback.message.edit_text(
        f"📎 Kirim file CSV untuk diimpor ke tabel <b>{table_name}</b>.\n"
        f"<b>Peringatan:</b> data lama akan dihapus.",
        parse_mode="HTML",
        reply_markup=back_to_data()
    )
    await callback.answer()


@router.message(AdminDataState.upload_file, F.document)
async def data_import_konfirmasi(message: types.Message, state: FSMContext, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        return

    document = message.document
    if not document.file_name.endswith(".csv"):
        await message.answer("❌ File harus berformat CSV.", reply_markup=back_to_data())
        return

    file = await bot.get_file(document.file_id)
    file_bytes = await bot.download_file(file.file_path)
    content = file_bytes.read().decode("utf-8")

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        await message.answer("❌ File CSV minimal harus ada header + 1 baris data.", reply_markup=back_to_data())
        return

    headers = rows[0]
    data_rows = rows[1:]

    await state.update_data(headers=headers, data_rows=data_rows)
    await state.set_state(AdminDataState.konfirmasi)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ya, Impor Sekarang".center(25), callback_data="import_confirm")
    builder.button(text="❌ Batal".center(25), callback_data="admin_set_data")
    builder.adjust(1)

    preview = "\n".join([", ".join(row) for row in data_rows[:5]])
    if len(data_rows) > 5:
        preview += f"\n... dan {len(data_rows) - 5} baris lainnya."

    data = await state.get_data()
    await message.answer(
        f"📋 <b>Preview Impor</b>\n"
        f"Tabel: {data.get('table_name')}\n"
        f"Jumlah baris: {len(data_rows)}\n\n"
        f"<pre>{preview}</pre>\n\n"
        f"Data lama akan <b>dihapus</b>. Lanjutkan?",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@router.callback_query(AdminDataState.konfirmasi, F.data == "import_confirm")
async def data_import_execute(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Akses ditolak.", show_alert=True)
        return

    data = await state.get_data()
    table_name = data.get("table_name")
    headers = data.get("headers")
    data_rows = data.get("data_rows")

    if not table_name or not headers or not data_rows:
        await callback.answer("Data tidak lengkap.", show_alert=True)
        return

    count = await import_csv_to_table(table_name, headers, data_rows)
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali ke Setting Data".center(25), callback_data="admin_set_data")
    builder.adjust(1)

    await callback.message.edit_text(
        f"✅ Impor ke tabel <b>{table_name}</b> berhasil!\n"
        f"{count} baris data telah dimasukkan.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ================= CANCEL =================
@router.message(F.command == "cancel")
async def data_cancel(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("Proses dibatalkan.", reply_markup=back_to_data())