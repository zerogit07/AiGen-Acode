from aiogram.fsm.state import State, StatesGroup

class AdminPageState(StatesGroup):
    menunggu_gambar_start = State()
    menunggu_gambar_menu = State()