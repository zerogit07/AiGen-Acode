from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_panel():
    builder = InlineKeyboardBuilder()

    # Baris 1
    builder.button(text="🔑 Setting API Key".center(25), callback_data="admin_set_api")
    builder.button(text="🌐 Setting Proxy".center(25), callback_data="admin_set_proxy")

    # Baris 2
    builder.button(text="👥 Setting Member".center(25), callback_data="admin_set_member")
    builder.button(text="🧠 Setting Model".center(25), callback_data="admin_set_model")

    # Baris 3
    builder.button(text="📊 Setting Limit".center(25), callback_data="admin_set_limit")
    builder.button(text="📄 Setting Page".center(25), callback_data="admin_set_page")

    # Baris 4
    builder.button(text="🗃️ Setting Data".center(25), callback_data="admin_set_data")
    builder.button(text="💬 Setting Message".center(25), callback_data="admin_set_message")

    # Baris 5
    builder.button(text="📈 Statistic".center(25), callback_data="admin_statistic")
    builder.button(text="🚪 Logout".center(25), callback_data="admin_logout")

    builder.adjust(2)  # 2 kolom
    return builder.as_markup()