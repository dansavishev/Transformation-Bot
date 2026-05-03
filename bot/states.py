from aiogram.fsm.state import State, StatesGroup


class UserFSM(StatesGroup):
    consent = State()
    choosing_mode = State()
    in_situation = State()
    in_trainer_answer = State()
