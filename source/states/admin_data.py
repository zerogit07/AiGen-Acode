from aiogram.fsm.state import State, StatesGroup

class AdminDataState(StatesGroup):
    pilih_tabel = State()
    upload_file = State()
    konfirmasi = State()