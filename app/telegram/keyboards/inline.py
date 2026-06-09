from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.core.constants import ActivityLevel, GoalType, GoalIntensity
from app.i18n.ua import (
    BTN_GENDER_MALE, BTN_GENDER_FEMALE,
    BTN_ACTIVITY_SEDENTARY, BTN_ACTIVITY_LIGHTLY_ACTIVE,
    BTN_ACTIVITY_MODERATELY, BTN_ACTIVITY_VERY_ACTIVE, BTN_ACTIVITY_ATHLETE,
    BTN_GOAL_LOSE, BTN_GOAL_MAINTAIN, BTN_GOAL_MUSCLE,
    BTN_INTENSITY_MILD, BTN_INTENSITY_MODERATE, BTN_INTENSITY_AGGRESSIVE,
    BTN_BULK_SLOW, BTN_BULK_MODERATE, BTN_BULK_AGGRESSIVE,
    BTN_SAVE, BTN_CANCEL, BTN_EDIT, BTN_SKIP, BTN_BACK,
    BTN_MENU_DASHBOARD, BTN_MENU_LOGFOOD, BTN_MENU_WEIGHT,
    BTN_MENU_STATS, BTN_MENU_PROFILE, BTN_MENU_GOAL,
    BTN_PHOTO_VERIFY_OK, BTN_PHOTO_VERIFY_WRONG,
)


def gender_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BTN_GENDER_MALE,   callback_data="gender:male"),
        InlineKeyboardButton(text=BTN_GENDER_FEMALE, callback_data="gender:female"),
    )
    return builder.as_markup()


def activity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_ACTIVITY_SEDENTARY,      callback_data="activity:sedentary")
    builder.button(text=BTN_ACTIVITY_LIGHTLY_ACTIVE, callback_data="activity:lightly_active")
    builder.button(text=BTN_ACTIVITY_MODERATELY,     callback_data="activity:moderately_active")
    builder.button(text=BTN_ACTIVITY_VERY_ACTIVE,    callback_data="activity:very_active")
    builder.button(text=BTN_ACTIVITY_ATHLETE,        callback_data="activity:athlete")
    builder.adjust(1)
    return builder.as_markup()


def goal_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BTN_GOAL_LOSE,     callback_data="goal:lose_weight"),
        InlineKeyboardButton(text=BTN_GOAL_MAINTAIN, callback_data="goal:maintain"),
        InlineKeyboardButton(text=BTN_GOAL_MUSCLE,   callback_data="goal:gain_muscle"),
    )
    builder.adjust(1)
    return builder.as_markup()


def weight_loss_intensity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_INTENSITY_MILD,       callback_data="intensity:mild")
    builder.button(text=BTN_INTENSITY_MODERATE,   callback_data="intensity:moderate")
    builder.button(text=BTN_INTENSITY_AGGRESSIVE, callback_data="intensity:aggressive")
    builder.adjust(1)
    return builder.as_markup()


def muscle_gain_intensity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_BULK_SLOW,       callback_data="intensity:slow")
    builder.button(text=BTN_BULK_MODERATE,   callback_data="intensity:fast")
    builder.button(text=BTN_BULK_AGGRESSIVE, callback_data="intensity:very_fast")
    builder.adjust(1)
    return builder.as_markup()


def photo_verify_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BTN_PHOTO_VERIFY_OK,    callback_data="photo_verify:ok"),
        InlineKeyboardButton(text=BTN_PHOTO_VERIFY_WRONG, callback_data="photo_verify:wrong"),
    )
    builder.adjust(2)
    return builder.as_markup()


def confirm_food_keyboard(entry_ids: list[str] | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BTN_SAVE,   callback_data="food_confirm:yes"),
        InlineKeyboardButton(text=BTN_CANCEL, callback_data="food_confirm:no"),
        InlineKeyboardButton(text=BTN_EDIT,   callback_data="food_confirm:edit"),
    )
    builder.adjust(2, 1)
    return builder.as_markup()


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_MENU_DASHBOARD, callback_data="menu:dashboard")
    builder.button(text=BTN_MENU_LOGFOOD,   callback_data="menu:logfood")
    builder.button(text=BTN_MENU_WEIGHT,    callback_data="menu:weight")
    builder.button(text=BTN_MENU_STATS,     callback_data="menu:stats")
    builder.button(text=BTN_MENU_PROFILE,   callback_data="menu:profile")
    builder.button(text=BTN_MENU_GOAL,      callback_data="menu:goal")
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def back_keyboard(callback: str = "menu:main") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_BACK, callback_data=callback)
    return builder.as_markup()


def skip_keyboard(callback: str = "skip") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_SKIP, callback_data=callback)
    return builder.as_markup()
