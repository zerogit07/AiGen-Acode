from aiogram.fsm.state import State, StatesGroup

class AdminApiKeyState(StatesGroup):
    tambah_key = State()
    reset_key = State()