"""
All nutrition science constants and formulas used throughout the application.

BMR Formula: Mifflin-St Jeor (1990) — most validated for general population.
  Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age_years) + 5
  Female: BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age_years) − 161

TDEE = BMR × activity_multiplier

Calorie deficit/surplus applied on top of TDEE to create goal-specific target.
Macros calculated from calorie target using evidence-based ratios.
"""

from enum import Enum


# ─── Activity Level ────────────────────────────────────────────────────────────

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"           # Desk job, no exercise
    LIGHTLY_ACTIVE = "lightly_active" # 1-3 days/week light exercise
    MODERATELY_ACTIVE = "moderately_active"  # 3-5 days/week moderate exercise
    VERY_ACTIVE = "very_active"       # 6-7 days/week hard exercise
    ATHLETE = "athlete"               # 2x/day training or physical job


ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.ATHLETE: 1.9,
}

ACTIVITY_LABELS: dict[ActivityLevel, str] = {
    ActivityLevel.SEDENTARY: "🪑 Sedentary (desk job, no exercise)",
    ActivityLevel.LIGHTLY_ACTIVE: "🚶 Lightly Active (1-3 days/week)",
    ActivityLevel.MODERATELY_ACTIVE: "🏃 Moderately Active (3-5 days/week)",
    ActivityLevel.VERY_ACTIVE: "💪 Very Active (6-7 days/week)",
    ActivityLevel.ATHLETE: "🏋️ Athlete (2x/day or physical job)",
}


# ─── Goal Types ────────────────────────────────────────────────────────────────

class GoalType(str, Enum):
    LOSE_WEIGHT = "lose_weight"
    MAINTAIN = "maintain"
    GAIN_MUSCLE = "gain_muscle"


class GoalIntensity(str, Enum):
    # Weight loss
    MILD = "mild"           # -250 kcal/day → ~0.25 kg/week loss
    MODERATE = "moderate"   # -500 kcal/day → ~0.50 kg/week loss
    AGGRESSIVE = "aggressive"  # -750 kcal/day → ~0.75 kg/week loss
    # Muscle gain
    SLOW = "slow"           # +200 kcal/day → ~0.20 kg/week gain
    FAST = "fast"           # +350 kcal/day → ~0.35 kg/week gain
    VERY_FAST = "very_fast" # +500 kcal/day → ~0.50 kg/week gain


# kcal/day adjustment from TDEE
CALORIE_ADJUSTMENTS: dict[GoalIntensity, int] = {
    GoalIntensity.MILD: -250,
    GoalIntensity.MODERATE: -500,
    GoalIntensity.AGGRESSIVE: -750,
    GoalIntensity.SLOW: 200,
    GoalIntensity.FAST: 350,
    GoalIntensity.VERY_FAST: 500,
}

GOAL_INTENSITY_LABELS: dict[GoalIntensity, str] = {
    GoalIntensity.MILD: "Mild deficit (−250 kcal/day, ~0.25 kg/week)",
    GoalIntensity.MODERATE: "Moderate deficit (−500 kcal/day, ~0.5 kg/week)",
    GoalIntensity.AGGRESSIVE: "Aggressive deficit (−750 kcal/day, ~0.75 kg/week)",
    GoalIntensity.SLOW: "Slow bulk (+200 kcal/day, ~0.2 kg/week)",
    GoalIntensity.FAST: "Moderate bulk (+350 kcal/day, ~0.35 kg/week)",
    GoalIntensity.VERY_FAST: "Aggressive bulk (+500 kcal/day, ~0.5 kg/week)",
}


# ─── Macronutrient Ratios ──────────────────────────────────────────────────────

# Protein: g/kg body weight (higher end for fat loss to preserve muscle)
PROTEIN_PER_KG: dict[GoalType, float] = {
    GoalType.LOSE_WEIGHT: 2.2,
    GoalType.GAIN_MUSCLE: 2.0,
    GoalType.MAINTAIN: 1.8,
}

# Fat as fraction of total calories
FAT_FRACTION = 0.275  # 27.5% of calories from fat

# Caloric density
KCAL_PER_GRAM_PROTEIN = 4.0
KCAL_PER_GRAM_CARB = 4.0
KCAL_PER_GRAM_FAT = 9.0


# ─── Gender ────────────────────────────────────────────────────────────────────

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


# ─── Meal Times ────────────────────────────────────────────────────────────────

class MealTime(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


# ─── Subscription Plans ────────────────────────────────────────────────────────

class SubscriptionPlan(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ─── Input Types ───────────────────────────────────────────────────────────────

class FoodInputType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VOICE = "voice"


# ─── AI Analysis Types ─────────────────────────────────────────────────────────

class AnalysisType(str, Enum):
    FOOD_TEXT = "food_text"
    FOOD_PHOTO = "food_photo"
    COACHING_DAILY = "coaching_daily"
    COACHING_EVENING = "coaching_evening"
    WEEKLY_SUMMARY = "weekly_summary"
    VOICE_TRANSCRIPTION = "voice_transcription"


# ─── UI Constants ──────────────────────────────────────────────────────────────

PROGRESS_BAR_LENGTH = 10
LOW_CONFIDENCE_THRESHOLD = 0.7

# Macro progress bar emoji
BAR_FILLED = "█"
BAR_EMPTY = "░"
