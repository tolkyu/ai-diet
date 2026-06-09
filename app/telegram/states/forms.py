from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_activity = State()


class GoalStates(StatesGroup):
    waiting_for_goal_type = State()
    waiting_for_intensity = State()
    waiting_for_target_weight = State()


class FoodLogStates(StatesGroup):
    waiting_for_food_input = State()
    waiting_for_clarification = State()
    waiting_for_photo_verification = State()
    waiting_for_photo_correction = State()
    waiting_for_confirmation = State()


class WeightStates(StatesGroup):
    waiting_for_weight = State()
    waiting_for_body_fat = State()


class ProfileEditStates(StatesGroup):
    waiting_for_field_value = State()
