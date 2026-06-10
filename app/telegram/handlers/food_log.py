from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PhotoSize, Voice
from app.telegram.states.forms import FoodLogStates
from app.telegram.keyboards.inline import confirm_food_keyboard, main_menu_keyboard, photo_verify_keyboard
from app.core.constants import FoodInputType, LOW_CONFIDENCE_THRESHOLD
from app.core.exceptions import QuotaExceededError
from app.core.logging import get_logger
from app.ai.nutrition_analyzer import FoodAnalysisResult, FoodItem
from app.i18n.ua import (
    FOOD_LOG_PROMPT, FOOD_ANALYZING_TEXT, FOOD_ANALYZING_PHOTO, FOOD_ANALYZING_VOICE,
    FOOD_TOO_SHORT, FOOD_ANALYSIS_ERROR_TEXT, FOOD_ANALYSIS_ERROR_PHOTO,
    FOOD_ANALYSIS_ERROR_VOICE, FOOD_VOICE_HEARD, FOOD_SHOULD_SAVE, FOOD_CLARIFICATION,
    FOOD_CANCELLED, FOOD_EDIT_PROMPT, FOOD_SAVED, FOOD_SAVED_ANSWER,
    FOOD_SESSION_EXPIRED, FOOD_RESULT_HEADER, FOOD_QUOTA_EXCEEDED_TEXT,
    FOOD_QUOTA_EXCEEDED_PHOTO, FOOD_START_FIRST, FOOD_CONFIDENCE, BTN_LOG_FOOD,
    FOOD_PHOTO_VERIFY, FOOD_PHOTO_CORRECTION_PROMPT, FOOD_PHOTO_REANALYZING,
    PAYWALL_LIMIT_REACHED, PAYWALL_BTN_SUBSCRIBE, FOOD_VOICE_PREMIUM_ONLY,
    PREMIUM_ANALYSIS_HEADER, PREMIUM_QUALITY_SCORE, PREMIUM_STRENGTHS,
    PREMIUM_WEAKNESSES, PREMIUM_RECOMMENDATION,
    MAIN_MENU_BUTTONS,
)

_MENU_BUTTONS = MAIN_MENU_BUTTONS

router = Router(name="food_log")
logger = get_logger(__name__)

_PENDING_RESULT_KEY = "pending_food_result"
_PENDING_TEXT_KEY   = "pending_food_text"


def _result_from_state(data) -> FoodAnalysisResult:
    """Reconstruct FoodAnalysisResult from a Redis-deserialized dict or return as-is."""
    if isinstance(data, FoodAnalysisResult):
        return data
    items = [
        FoodItem(
            name=i["name"],
            amount_g=i.get("amount_g"),
            calories=float(i["calories"]),
            protein_g=float(i["protein_g"]),
            fat_g=float(i["fat_g"]),
            carbs_g=float(i["carbs_g"]),
            confidence_score=float(i.get("confidence_score", 0.8)),
            notes=i.get("notes"),
        )
        for i in data.get("items", [])
    ]
    result = FoodAnalysisResult(
        items=items,
        total_calories=float(data.get("total_calories", 0)),
        total_protein_g=float(data.get("total_protein_g", 0)),
        total_fat_g=float(data.get("total_fat_g", 0)),
        total_carbs_g=float(data.get("total_carbs_g", 0)),
        overall_confidence=float(data.get("overall_confidence", 0.8)),
        clarification_needed=bool(data.get("clarification_needed", False)),
        clarification_question=data.get("clarification_question"),
    )
    for attr in ("meal_type_guess", "food_quality_note", "quality_score", "strengths", "weaknesses", "recommendation"):
        if attr in data:
            setattr(result, attr, data[attr])
    return result


def _format_food_summary(result, is_premium: bool = False) -> str:
    header = PREMIUM_ANALYSIS_HEADER if is_premium else FOOD_RESULT_HEADER
    lines = [header, ""]
    for item in result.items:
        amount = f"{item.amount_g:.0f}г " if item.amount_g else ""
        lines.append(
            f"• {amount}<b>{item.name}</b>\n"
            f"  {item.calories:.0f} ккал | Б: {item.protein_g:.0f}г | Ж: {item.fat_g:.0f}г | В: {item.carbs_g:.0f}г"
        )

    lines += [
        "",
        "─────────────────",
        f"<b>Всього: {result.total_calories:.0f} ккал</b>",
        f"Білки: {result.total_protein_g:.0f}г | Жири: {result.total_fat_g:.0f}г | Вуглеводи: {result.total_carbs_g:.0f}г",
        "",
        FOOD_CONFIDENCE.format(pct=result.overall_confidence * 100),
    ]

    if is_premium:
        score = getattr(result, "quality_score", None)
        if score:
            lines.append(PREMIUM_QUALITY_SCORE.format(score=score))
        strengths = getattr(result, "strengths", []) or []
        if strengths:
            lines.append(PREMIUM_STRENGTHS)
            lines.extend(f"  • {s}" for s in strengths)
        weaknesses = getattr(result, "weaknesses", []) or []
        if weaknesses:
            lines.append(PREMIUM_WEAKNESSES)
            lines.extend(f"  • {w}" for w in weaknesses)
        recommendation = getattr(result, "recommendation", None)
        if recommendation:
            lines.append(PREMIUM_RECOMMENDATION.format(text=recommendation))

    return "\n".join(lines)


@router.message(Command("logfood"))
@router.message(F.text == BTN_LOG_FOOD)
async def cmd_logfood(message: Message, state: FSMContext) -> None:
    await state.set_state(FoodLogStates.waiting_for_food_input)
    await message.answer(FOOD_LOG_PROMPT, parse_mode="HTML")


@router.message(FoodLogStates.waiting_for_food_input, F.text, ~F.text.in_(_MENU_BUTTONS))
async def handle_text_food(message: Message, state: FSMContext) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.food_log_service import FoodLogService
    from app.ai.nutrition_analyzer import nutrition_analyzer

    text = message.text.strip()  # type: ignore[union-attr]
    if len(text) < 3:
        await message.answer(FOOD_TOO_SHORT)
        return

    processing_msg = await message.answer(FOOD_ANALYZING_TEXT)

    try:
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            food_log_svc = FoodLogService(session)
            user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
            if not user:
                await processing_msg.edit_text(FOOD_START_FIRST)
                return

            try:
                await food_log_svc.check_and_increment_quota(user.id, FoodInputType.TEXT)
            except QuotaExceededError:
                await processing_msg.edit_text(FOOD_QUOTA_EXCEEDED_TEXT)
                await state.clear()
                return

            result = await nutrition_analyzer.analyze_text(
                text, user_id=user.id, session=session
            )
            await session.commit()
    except Exception as e:
        logger.error("Food analysis failed", error=str(e))
        await processing_msg.edit_text(FOOD_ANALYSIS_ERROR_TEXT)
        return

    if result.clarification_needed:
        await state.update_data(**{_PENDING_RESULT_KEY: result, _PENDING_TEXT_KEY: text})
        await processing_msg.edit_text(
            _format_food_summary(result) + FOOD_CLARIFICATION.format(question=result.clarification_question),
            parse_mode="HTML",
        )
        await state.set_state(FoodLogStates.waiting_for_clarification)
        return

    await state.update_data(**{_PENDING_RESULT_KEY: result, _PENDING_TEXT_KEY: text})
    await processing_msg.edit_text(
        _format_food_summary(result) + FOOD_SHOULD_SAVE,
        parse_mode="HTML",
        reply_markup=confirm_food_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_confirmation)


@router.message(FoodLogStates.waiting_for_food_input, F.photo)
async def handle_photo_food(message: Message, state: FSMContext) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.food_log_service import FoodLogService
    from app.ai.food_photo_analyzer import food_photo_analyzer

    processing_msg = await message.answer(FOOD_ANALYZING_PHOTO)

    photo: PhotoSize = message.photo[-1]  # type: ignore[index]
    file = await message.bot.get_file(photo.file_id)  # type: ignore[union-attr]
    photo_bytes_io = await message.bot.download_file(file.file_path)  # type: ignore[union-attr]
    photo_bytes = photo_bytes_io.read()  # type: ignore[union-attr]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        food_log_svc = FoodLogService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if not user:
            await processing_msg.edit_text(FOOD_START_FIRST)
            return

        from app.services.subscription_service import SubscriptionService
        sub_svc = SubscriptionService(session)
        sub_info = await sub_svc.get_usage_info(user.id, telegram_id=message.from_user.id)  # type: ignore[union-attr]
        is_premium = sub_info["plan"] == "premium"

        try:
            await food_log_svc.check_and_increment_quota(user.id, FoodInputType.PHOTO)
        except QuotaExceededError:
            from aiogram.types import InlineKeyboardButton
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.add(InlineKeyboardButton(text=PAYWALL_BTN_SUBSCRIBE, callback_data="go:subscribe"))
            await processing_msg.edit_text(
                PAYWALL_LIMIT_REACHED,
                parse_mode="HTML",
                reply_markup=builder.as_markup(),
            )
            await state.clear()
            return

        try:
            result = await food_photo_analyzer.analyze_photo(
                photo_bytes, user_id=user.id, session=session, is_premium=is_premium
            )
            await session.commit()
        except Exception as e:
            logger.error("Photo analysis failed", error=str(e))
            await processing_msg.edit_text(FOOD_ANALYSIS_ERROR_PHOTO)
            return

    await state.update_data(**{_PENDING_RESULT_KEY: result, _PENDING_TEXT_KEY: "photo", "is_premium": is_premium})
    await processing_msg.edit_text(
        _format_food_summary(result, is_premium) + FOOD_PHOTO_VERIFY,
        parse_mode="HTML",
        reply_markup=photo_verify_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_photo_verification)


@router.callback_query(FoodLogStates.waiting_for_photo_verification, F.data == "photo_verify:ok")
async def photo_verify_ok(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    result = _result_from_state(data.get(_PENDING_RESULT_KEY)) if data.get(_PENDING_RESULT_KEY) else None
    is_premium = data.get("is_premium", False)
    if not result:
        await callback.answer()
        await state.clear()
        return
    await callback.message.edit_text(  # type: ignore[union-attr]
        _format_food_summary(result, is_premium) + FOOD_SHOULD_SAVE,
        parse_mode="HTML",
        reply_markup=confirm_food_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_confirmation)
    await callback.answer()


@router.callback_query(FoodLogStates.waiting_for_photo_verification, F.data == "photo_verify:wrong")
async def photo_verify_wrong(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_text(FOOD_PHOTO_CORRECTION_PROMPT, parse_mode="HTML")  # type: ignore[union-attr]
    await state.set_state(FoodLogStates.waiting_for_photo_correction)
    await callback.answer()


@router.message(FoodLogStates.waiting_for_photo_correction, F.text, ~F.text.in_(_MENU_BUTTONS))
async def handle_photo_correction(message: Message, state: FSMContext) -> None:
    from app.ai.food_photo_analyzer import food_photo_analyzer

    data = await state.get_data()
    initial_result = _result_from_state(data.get(_PENDING_RESULT_KEY)) if data.get(_PENDING_RESULT_KEY) else None
    is_premium = data.get("is_premium", False)
    if not initial_result:
        await state.clear()
        return

    processing_msg = await message.answer(FOOD_PHOTO_REANALYZING)

    try:
        refined_result = await food_photo_analyzer.analyze_photo_with_followup(
            photo_bytes=b"",
            followup_answer=message.text,  # type: ignore[arg-type]
            initial_result=initial_result,
            is_premium=is_premium,
        )
    except Exception as e:
        logger.error("Photo correction re-analysis failed", error=str(e))
        refined_result = initial_result

    await state.update_data(**{_PENDING_RESULT_KEY: refined_result})
    await processing_msg.edit_text(
        _format_food_summary(refined_result, is_premium) + FOOD_PHOTO_VERIFY,
        parse_mode="HTML",
        reply_markup=photo_verify_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_photo_verification)


@router.message(FoodLogStates.waiting_for_food_input, F.voice)
async def handle_voice_food(message: Message, state: FSMContext) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.subscription_service import SubscriptionService
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_svc = SubscriptionService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if user:
            sub_info = await sub_svc.get_usage_info(user.id, telegram_id=message.from_user.id)  # type: ignore[union-attr]
            is_premium = sub_info["plan"] == "premium"
        else:
            is_premium = False

    if not is_premium:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text=PAYWALL_BTN_SUBSCRIBE, callback_data="go:subscribe"))
        await message.answer(FOOD_VOICE_PREMIUM_ONLY, parse_mode="HTML", reply_markup=builder.as_markup())
        return

    from app.ai.voice_processor import voice_processor

    processing_msg = await message.answer(FOOD_ANALYZING_VOICE)
    voice: Voice = message.voice  # type: ignore[assignment]
    file = await message.bot.get_file(voice.file_id)  # type: ignore[union-attr]
    audio_io = await message.bot.download_file(file.file_path)  # type: ignore[union-attr]
    audio_bytes = audio_io.read()  # type: ignore[union-attr]

    try:
        transcribed, result = await voice_processor.process_voice_to_food(audio_bytes)
        await processing_msg.edit_text(
            FOOD_VOICE_HEARD.format(text=transcribed), parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Voice processing failed", error=str(e))
        await processing_msg.edit_text(FOOD_ANALYSIS_ERROR_VOICE)
        return

    await state.update_data(**{_PENDING_RESULT_KEY: result, _PENDING_TEXT_KEY: transcribed})

    if result.clarification_needed:
        await message.answer(
            _format_food_summary(result) + FOOD_CLARIFICATION.format(question=result.clarification_question),
            parse_mode="HTML",
        )
        await state.set_state(FoodLogStates.waiting_for_clarification)
        return

    await message.answer(
        _format_food_summary(result) + FOOD_SHOULD_SAVE,
        parse_mode="HTML",
        reply_markup=confirm_food_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_confirmation)


@router.message(FoodLogStates.waiting_for_clarification, F.text, ~F.text.in_(_MENU_BUTTONS))
async def handle_clarification(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    initial_result = _result_from_state(data.get(_PENDING_RESULT_KEY)) if data.get(_PENDING_RESULT_KEY) else None
    if not initial_result:
        await state.clear()
        return

    from app.ai.food_photo_analyzer import food_photo_analyzer
    try:
        refined_result = await food_photo_analyzer.analyze_photo_with_followup(
            photo_bytes=b"",
            followup_answer=message.text,  # type: ignore[arg-type]
            initial_result=initial_result,
        )
    except Exception:
        refined_result = initial_result

    await state.update_data(**{_PENDING_RESULT_KEY: refined_result})
    await message.answer(
        _format_food_summary(refined_result) + FOOD_SHOULD_SAVE,
        parse_mode="HTML",
        reply_markup=confirm_food_keyboard(),
    )
    await state.set_state(FoodLogStates.waiting_for_confirmation)


@router.callback_query(FoodLogStates.waiting_for_confirmation, F.data.startswith("food_confirm:"))
async def handle_food_confirmation(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":")[1]  # type: ignore[union-attr]

    if action == "no":
        await callback.message.edit_text(FOOD_CANCELLED)  # type: ignore[union-attr]
        await state.clear()
        await callback.answer()
        return

    if action == "edit":
        await callback.message.edit_text(FOOD_EDIT_PROMPT)  # type: ignore[union-attr]
        await state.set_state(FoodLogStates.waiting_for_food_input)
        await callback.answer()
        return

    data = await state.get_data()
    result = _result_from_state(data.get(_PENDING_RESULT_KEY)) if data.get(_PENDING_RESULT_KEY) else None
    raw_input = data.get(_PENDING_TEXT_KEY, "")
    if not result:
        await callback.answer(FOOD_SESSION_EXPIRED)
        await state.clear()
        return

    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.food_log_service import FoodLogService
    from app.ai.nutrition_analyzer import NutritionAnalyzer

    try:
        async with AsyncSessionLocal() as session:
            user_repo = UserRepository(session)
            food_log_svc = FoodLogService(session)
            user = await user_repo.get_by_telegram_id(callback.from_user.id)
            if not user:
                await callback.answer()
                return

            entries_data = NutritionAnalyzer().format_entries_for_db(result)
            food_log, entries = await food_log_svc.add_food_entries(
                user_id=user.id,
                entries_data=entries_data,
                raw_input=raw_input if raw_input != "photo" else None,
                input_type=FoodInputType.PHOTO if raw_input == "photo" else FoodInputType.TEXT,
            )
            await session.commit()
    except Exception as e:
        logger.error("Food save failed", error=str(e))
        await callback.message.edit_text("Помилка при збереженні їжі. Спробуй ще раз.")  # type: ignore[union-attr]
        await callback.answer()
        await state.clear()
        return

    await callback.message.edit_text(  # type: ignore[union-attr]
        FOOD_SAVED.format(
            calories=result.total_calories,
            total_cal=float(food_log.total_calories),
            protein=float(food_log.total_protein_g),
            fat=float(food_log.total_fat_g),
            carbs=float(food_log.total_carbs_g),
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer(FOOD_SAVED_ANSWER)
