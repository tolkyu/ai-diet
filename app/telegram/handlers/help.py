from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from app.telegram.keyboards.inline import main_menu_keyboard
from app.i18n.ua import HELP_TEXT, BTN_HELP

router = Router(name="help")


@router.message(Command("help"))
@router.message(F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=main_menu_keyboard())
