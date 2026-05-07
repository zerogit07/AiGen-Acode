import base64
from aiogram import Router, F, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from source.services.job_manager import JobManager
from source.services.backend_models.kling_2_1_std import Kling21Std
from source.services.backend_models.kling_2_1_pro import Kling21Pro

router = Router()

class Kling21State(StatesGroup):
    pilih_resolusi = State()
    pilih_durasi = State()
    input_image = State()
    input_image_tail = State()
    input_prompt = State()

async def file_id_to_base64(bot: Bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file.file_path)
    return base64.b64encode(file_bytes.read()).decode("utf-8")

# --- Handler untuk tombol Kembali ke menu utama ---
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
    from source.keyboards.inlinestart import menu_utama
    await callback.message.edit_text(
        "<b>🤖 Menu Utama</b>",
        parse_mode="HTML",
        reply_markup=await menu_utama(callback.from_user.id, is_admin=False)
    )
    await callback.answer()

def back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Kembali", callback_data="model_kling_21")
    return builder.as_markup()

@router.callback_query(F.data == "model_kling_21")
async def kling21_start(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(resolusi=None, durasi=None)
    await show_resolution_duration_menu(callback, state)

async def show_resolution_duration_menu(callback: types.CallbackQuery, state: FSMContext):
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
    builder.adjust(2, 2, 1)
    await callback.message.edit_text(
        "🎬 <b>Kling 2.1</b>\nSilakan pilih resolusi dan durasi:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

@router.callback_query(Kling21State.pilih_resolusi, F.data.startswith("kling_res_"))
async def kling21_resolusi(callback: types.CallbackQuery, state: FSMContext):
    resolusi = callback.data.replace("kling_res_", "")
    await state.update_data(resolusi=resolusi, is_pro=(resolusi == "1080"))
    data = await state.get_data()
    if data.get("durasi"):
        await state.set_state(Kling21State.input_image)
        await callback.message.edit_text(
            "📎 Kirim gambar <b>first frame</b> (wajib).",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        await show_resolution_duration_menu(callback, state)
    await callback.answer()

@router.callback_query(F.data.startswith("kling_dur_"))
async def kling21_durasi(callback: types.CallbackQuery, state: FSMContext):
    durasi = callback.data.replace("kling_dur_", "")
    await state.update_data(durasi=durasi)
    data = await state.get_data()
    if data.get("resolusi"):
        await state.set_state(Kling21State.input_image)
        await callback.message.edit_text(
            "📎 Kirim gambar <b>first frame</b> (wajib).",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        await show_resolution_duration_menu(callback, state)
    await callback.answer()

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

    # 1. Kirim pesan "Submitting..." dan simpan ID-nya
    progress_msg = await message.answer("⏳ Submitting generation...")
    progress_msg_id = progress_msg.message_id  # Simpan ID pesan

    # 2. Siapkan data
    data = await state.get_data()
    user_id = message.from_user.id
    is_pro = data["is_pro"]
    durasi = data.get("durasi", "5")

    image_base64 = await file_id_to_base64(bot, data["image"])
    image_tail_base64 = None
    if data.get("image_tail"):
        image_tail_base64 = await file_id_to_base64(bot, data["image_tail"])

    model = Kling21Pro() if is_pro else Kling21Std()
    payload = {
        "image": image_base64,
        "prompt": data.get("prompt", ""),
        "duration": durasi
    }
    if image_tail_base64:
        payload["image_tail"] = image_tail_base64

    # 3. Kirim ke JobManager
    job_data = {
        "user_id": user_id,
        "model": model,
        "params": payload,
        "progress_msg_id": progress_msg_id  # ID pesan untuk di-update
    }
    await JobManager().enqueue(job_data)
    await state.clear()