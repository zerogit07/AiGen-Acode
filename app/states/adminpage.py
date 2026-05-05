from aiogram.fsm.state import State, StatesGroup

class AdminPageState(StatesGroup):
    menunggu_banner = State()
    menunggu_qris = State()
    menunggu_deskripsi = State()