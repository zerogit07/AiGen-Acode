from aiogram.fsm.state import State, StatesGroup

class AdminLimitState(StatesGroup):
    pilih_paket = State()
    input_process = State()
    input_daily = State()