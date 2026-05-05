from aiogram.fsm.state import State, StatesGroup

class DaftarState(StatesGroup):
    menunggu_bukti = State()
    menunggu_alasan = State()