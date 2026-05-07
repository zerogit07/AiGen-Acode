# app/handlers/frontend_models/kling_2_1.py

import base64
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.services.job_manager import JobManager
from app.services.backend_models.kling_2_1_std import Kling21Std
from app.services.backend_models.kling_2_1_pro import Kling21Pro

router = Router()

# ---------- FSM States ----------
class Kling21State(StatesGroup):
    pilih_resolusi = State()
    pilih_durasi = State()
    input_image = State()
    input_image_tail = State()
    input_prompt = State()

# ---------- Fungsi Pembantu ----------
async def file_id_to_base64(bot: Bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    return base64.b64encode(file_bytes.read()).decode("utf-8")

async def execute_video(event, user_id: int, state: FSMContext, bot: Bot):
    """Menyiapkan payload, memilih model, lalu mengirim ke JobManager."""
    data = await state.get_data()
    is_pro = data["is_pro"]
    durasi = data.get("durasi", "5")

    # Konversi gambar
    image_base64 = await file_id_to_base64(bot, data["image"])
    image_tail_base64 = None
    if data.get("image_tail"):
        image_tail_base64 = await file_id_to_base64(bot, data["image_tail"])

    # Pilih model
    model = Kling21Pro() if is_pro else Kling21Std()
    payload = {
        "image": image_base64,
        "prompt": data.get("prompt", ""),
        "duration": durasi
    }
    if image_tail_base64:
        payload["image_tail"] = image_tail_base64

    job_data = {
        "user_id": user_id,
        "model": model,
        "params": payload
    }
    await JobManager().enqueue(job_data)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text("✅ Video sedang dibuat! Kamu akan menerima notifikasi setelah selesai.")
    else:
        await event.answer("✅ Video sedang dibuat! Kamu akan menerima notifikasi setelah selesai.")
    await state.clear()

# ========== KEYBOARD ==========
def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="model_kling_21")
    return builder.as_markup()

# ========== START ==========
@router.callback_query(F.data == "model_kling_21")
async def kling21_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(resolusi=None, durasi=None)  # reset pilihan
    await show_resolution_duration_menu(callback, state)

async def show_resolution_duration_menu(callback: types.CallbackQuery, state: FSMContext):
    """Menampilkan dua baris tombol: resolusi dan durasi."""
    await state.set_state(Kling21State.pilih_resolusi)
    data = await state.get_data()

    builder = InlineKeyboardBuilder()
    builder.button(
        text="720p Standard" + (" ✅" if data.get("resolusi") == "720" else ""),
        callback_data="kling_res_720"
    )
    builder.button(
        text="1080p Pro" + (" ✅" if data.get("resolusi") == "1080" else ""),
        callback_data="kling_res_1080"
    )
    builder.button(
        text="5 detik" + (" ✅" if data.get("durasi") == "5" else ""),
        callback_data="kling_dur_5"
    )
    builder.button(
        text="10 detik" + (" ✅" if data.get("durasi") == "10" else ""),
        callback_data="kling_dur_10"
    )
    builder.button(text="🔙 Kembali", callback_data="main_menu")
    builder.adjust(2, 2, 1)  # 2 resolusi, 2 durasi, 1 kembali

    await callback.message.edit_text(
        "🎬 <b>Kling 2.1</b>\nSilakan pilih resolusi dan durasi:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# ========== PILIH RESOLUSI ==========
@router.callback_query(Kling21State.pilih_resolusi, F.data.startswith("kling_res_"))
async def kling21_resolusi(callback: types.CallbackQuery, state: FSMContext):
    resolusi = callback.data.replace("kling_res_", "")
    await state.update_data(resolusi=resolusi, is_pro=(resolusi == "1080"))
    data = await state.get_data()
    # Cek apakah durasi sudah dipilih
    if data.get("durasi"):
        # Jika sudah, lanjut ke input gambar
        await state.set_state(Kling21State.input_image)
        await callback.message.edit_text(
            "📎 Kirim gambar <b>first frame</b> (wajib).",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        # Tampilkan ulang menu resolusi+durasi
        await show_resolution_duration_menu(callback, state)
    await callback.answer()

# ========== PILIH DURASI ==========
@router.callback_query(F.data.startswith("kling_dur_"))
async def kling21_durasi(callback: types.CallbackQuery, state: FSMContext):
    durasi = callback.data.replace("kling_dur_", "")
    await state.update_data(durasi=durasi)
    data = await state.get_data()
    # Cek apakah resolusi sudah dipilih
    if data.get("resolusi"):
        # Jika sudah, lanjut ke input gambar
        await state.set_state(Kling21State.input_image)
        await callback.message.edit_text(
            "📎 Kirim gambar <b>first frame</b> (wajib).",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        # Tampilkan ulang menu resolusi+durasi
        await show_resolution_duration_menu(callback, state)
    await callback.answer()

# ========== Kembali menu utama ==========
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    # Bersihkan state FSM jika ada yang sedang berjalan
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    
    # Kirim ulang menu utama
    from app.keyboards.inlinestart import menu_utama
    await callback.message.edit_text(
        "<b>🤖 Menu Utama</b>",
        parse_mode="HTML",
        reply_markup=await menu_utama(callback.from_user.id, is_admin=False)
    )
    await callback.answer()

# ========== INPUT IMAGE (first frame) ==========
@router.message(Kling21State.input_image, F.photo)
async def kling21_image(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(image=file_id)
    data = await state.get_data()
    if data["is_pro"]:
        await state.set_state(Kling21State.input_image_tail)
        builder = InlineKeyboardBuilder()
        builder.button(text="Lewati", callback_data="skip_image_tail")
        builder.button(text="🔙 Kembali", callback_data="back_to_start")
        builder.adjust(2)
        await message.answer(
            "📎 Kirim gambar <b>end frame</b> (opsional), atau klik Lewati.",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await state.set_state(Kling21State.input_prompt)
        await message.answer(
            "✍️ Kirim prompt (wajib, minimal 5 karakter).",
            reply_markup=back_keyboard()
        )

@router.message(Kling21State.input_image)
async def kling21_image_invalid(message: types.Message):
    await message.answer("❌ Harap kirim gambar, bukan teks.")

# ========== INPUT IMAGE TAIL (PRO ONLY) ==========
@router.callback_query(Kling21State.input_image_tail, F.data == "skip_image_tail")
async def kling21_skip_tail(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(image_tail=None)
    await state.set_state(Kling21State.input_prompt)
    await callback.message.edit_text(
        "✍️ Kirim prompt (wajib, minimal 5 karakter).",
        reply_markup=back_keyboard()
    )
    await callback.answer()

@router.message(Kling21State.input_image_tail, F.photo)
async def kling21_image_tail(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(image_tail=file_id)
    await state.set_state(Kling21State.input_prompt)
    await message.answer(
        "✍️ Kirim prompt (wajib, minimal 5 karakter).",
        reply_markup=back_keyboard()
    )

# ========== INPUT PROMPT (SEKALIGUS EKSEKUSI) ==========
@router.message(Kling21State.input_prompt, F.text)
async def kling21_prompt_and_execute(message: types.Message, state: FSMContext, bot: Bot):
    prompt = message.text.strip()
    if len(prompt) < 5:
        await message.answer("❌ Prompt wajib diisi minimal 5 karakter.")
        return
    await state.update_data(prompt=prompt)
    await execute_video(message, message.from_user.id, state, bot)