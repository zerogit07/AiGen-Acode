from aiogram.utils.keyboard import InlineKeyboardBuilder

def menu_utama():
    builder = InlineKeyboardBuilder()

    # Baris 1
    builder.button(text="🎬 Kling V3".center(25), callback_data="model_kling_v3")
    builder.button(text="🚀 Kling V3 Motion".center(25), callback_data="model_kling_v3_motion")

    # Baris 2
    builder.button(text="🌀 Kling V3 Omni".center(25), callback_data="model_kling_v3_omni")
    builder.button(text="⚡ Kling 2.6 Pro".center(25), callback_data="model_kling_26_pro")

    # Baris 3
    builder.button(text="💨 Kling 2.6 Motion".center(25), callback_data="model_kling_26_motion")
    builder.button(text="🔥 Kling 2.5 Turbo".center(25), callback_data="model_kling_25_turbo")

    # Baris 4
    builder.button(text="🎯 Kling 2.1".center(25), callback_data="model_kling_21")
    builder.button(text="🧠 Kling O1".center(25), callback_data="model_kling_o1")

    # Baris 5
    builder.button(text="🌌 Veo 3.1".center(25), callback_data="model_veo_31")
    builder.button(text="🍌 Nano Banana".center(25), callback_data="model_nano_banana")

    builder.adjust(2)
    return builder.as_markup()