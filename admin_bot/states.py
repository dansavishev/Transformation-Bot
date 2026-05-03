from aiogram.fsm.state import State, StatesGroup


class AdminFSM(StatesGroup):
    main_menu = State()
    viewing_dialogs = State()
    viewing_user_dialog = State()
    editing_prompt = State()
    waiting_prompt_text = State()
    knowledge_menu = State()
    waiting_document = State()
    waiting_delete_number = State()
    viewing_summaries = State()
    viewing_changelog_entry = State()
    editing_changelog = State()
