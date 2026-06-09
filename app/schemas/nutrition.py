from pydantic import BaseModel, Field


class NutritionTargetsSchema(BaseModel):
    bmr: float
    tdee: float
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


class MacroProgressSchema(BaseModel):
    calories_consumed: float = 0
    calories_target: float
    calories_remaining: float
    protein_g_consumed: float = 0
    protein_g_target: float
    fat_g_consumed: float = 0
    fat_g_target: float
    carbs_g_consumed: float = 0
    carbs_g_target: float

    @property
    def calorie_pct(self) -> float:
        return (self.calories_consumed / self.calories_target * 100) if self.calories_target else 0
