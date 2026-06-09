from pydantic import BaseModel, Field


class FoodItemSchema(BaseModel):
    name: str
    amount_g: float | None = None
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float
    confidence_score: float = Field(default=0.8, ge=0, le=1)
    notes: str | None = None


class FoodAnalysisResponseSchema(BaseModel):
    items: list[FoodItemSchema]
    total_calories: float
    total_protein_g: float
    total_fat_g: float
    total_carbs_g: float
    overall_confidence: float
    clarification_needed: bool = False
    clarification_question: str | None = None
