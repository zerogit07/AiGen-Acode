from aiogram.fsm.state import State, StatesGroup

class AdminProxyState(StatesGroup):
    tambah_proxy = State()
    reset_proxy = State()