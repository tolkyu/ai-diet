from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from app.i18n.ua import BTN_DASHBOARD, BTN_LOG_FOOD, BTN_WEIGHT, BTN_STATS, BTN_PROFILE, BTN_HELP, BTN_WATER


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=BTN_DASHBOARD),
        KeyboardButton(text=BTN_LOG_FOOD),
        KeyboardButton(text=BTN_WEIGHT),
        KeyboardButton(text=BTN_WATER),
        KeyboardButton(text=BTN_STATS),
        KeyboardButton(text=BTN_PROFILE),
        KeyboardButton(text=BTN_HELP),
    )
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True, persistent=True)


def remove_keyboard() -> ReplyKeyboardMarkup:
    from aiogram.types import ReplyKeyboardRemove
    return ReplyKeyboardRemove()  # type: ignore[return-value]
