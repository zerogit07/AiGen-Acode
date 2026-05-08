from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from source.states.daftar_state import DaftarState
from source.keyboards.inlinedaftar import daftar_keyboard
from source.keyboards.inlinenonmember import nonmember_keyboard
from source.utils.gambar_page import ambil_gambar, ambil_deskripsi, ambil_harga
from source.config import ADMIN_ID


router = Router()

# === TOMBOL PAKET DARI HALAMAN NON‑MEMBER ===
@router.callback_query(F.data.in_({"register_lite", "register_pro", "register_ultra"}))
async def daftar_pilih_paket(callback: types.CallbackQuery):
    paket = callback.data.replace("register_", "").capitalize()
    deskripsi = ambil_deskripsi(paket.lower())
    if not deskripsi:
        deskripsi = f"Paket {paket} - Deskripsi belum diatur oleh admin."

    harga_dasar = ambil_harga(paket.lower())
    kode_unik = int(str(callback.from_user.id)[-3:])

    if harga_dasar is not None:
        total = harga_dasar + kode_unik
        total_str = f"Rp {total:,}".replace(",", ".")
    else:
        total_str = "Harga belum diatur"

    qris = ambil_gambar("qris")

    caption = (
        f"📦 <b>Paket {paket}</b>\n"
        f"{deskripsi}\n\n"
        f"💰 Harga: <b>{total_str}</b>\n\n"
        f"Silakan lakukan pembayaran ke QRIS di atas."
    )

    # Hapus pesan non‑member (yang berisi tombol Lite/Pro/Ultra)
    await callback.message.delete()

    if qris:
        await callback.message.answer_photo(
            photo=qris,
            caption=caption,
            parse_mode="HTML",
            reply_markup=daftar_keyboard(paket)
        )
    else:
        await callback.message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=daftar_keyboard(paket)
        )
    await callback.answer()

# === TOMBOL KEMBALI ===
@router.callback_query(F.data == "kembali_nonmember")
async def daftar_kembali(callback: types.CallbackQuery):
    # Hapus pesan detail paket (bisa foto / teks)
    await callback.message.delete()
    # Kirim ulang halaman non‑member
    deskripsi_banner = ambil_deskripsi("banner")
    if not deskripsi_banner:
        deskripsi_banner = "Maaf, kamu belum terdaftar.\nSilakan pilih paket pendaftaran di bawah ini:"
    await callback.message.answer(
        deskripsi_banner,
        reply_markup=nonmember_keyboard()
    )
    await callback.answer()
    
# === TOMBOL KIRIM BUKTI ===
@router.callback_query(F.data.startswith("kirim_bukti_"))
async def daftar_minta_bukti(callback: types.CallbackQuery, state: FSMContext):
    paket = callback.data.replace("kirim_bukti_", "").capitalize()
    await state.set_state(DaftarState.menunggu_bukti)
    await state.update_data(paket=paket)
    await callback.message.answer("📎 Kirim foto bukti pembayaran kamu sekarang.")
    await callback.answer()

# === TERIMA FOTO BUKTI ===
@router.message(DaftarState.menunggu_bukti, F.photo)
async def daftar_terima_bukti(message: types.Message, state: FSMContext, bot):
    data = await state.get_data()
    paket = data["paket"]
    user = message.from_user

    # Ambil harga dasar
    harga_dasar = ambil_harga(paket.lower())
    # Ambil 3 digit terakhir User ID
    kode_unik = int(str(user.id)[-3:])
    # Hitung total
    if harga_dasar is not None:
        total = harga_dasar + kode_unik
        harga_str = f"Rp {total:,}".replace(",", ".")
    else:
        harga_str = "Harga belum diatur"

    # Kirim ke admin
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Setujui".center(25), callback_data=f"approve_{user.id}_{paket}")
    builder.button(text="❌ Tolak".center(25), callback_data=f"reject_{user.id}_{paket}")
    builder.adjust(1)

    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=(
            f"📩 <b>Bukti Pembayaran</b>\n"
            f"User ID: <code>{user.id}</code>\n"
            f"Username: @{user.username or '-'}\n"
            f"Paket: {paket}\n"
            f"Harga: <b>{harga_str}</b>"
        ),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await message.answer("✅ Bukti kamu sudah dikirim ke admin. Tunggu konfirmasi.")
    await state.clear()