from aiogram.fsm.state import State, StatesGroup

class MemberState(StatesGroup):
    pilih_paket = State()
    masukkan_userid = State()
    cari_userid = State()
    ubah_paket = State()