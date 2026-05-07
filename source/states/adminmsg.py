from aiogram.fsm.state import State, StatesGroup

class AdminMsgState(StatesGroup):
    # Broadcast
    pilih_target = State()
    tulis_pesan = State()
    konfirmasi = State()

    # Privat Message
    input_userid = State()
    tulis_privat = State()
    konfirmasi_privat = State()