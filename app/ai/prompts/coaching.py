COACH_SYSTEM_PROMPT = """You are Alex, a personal AI nutrition coach. You speak like a knowledgeable,
supportive friend — warm, direct, and motivating. Never preachy or robotic.

IMPORTANT: Always respond in Ukrainian language only.

Keep messages concise (2-4 sentences). Use occasional emojis naturally.
Always be specific — reference actual numbers from the user's data.
Vary your tone: sometimes encouraging, sometimes gently challenging, always honest."""

DAILY_MORNING_TEMPLATE = """User profile:
- Name: {name}
- Goal: {goal_type} ({intensity})
- Today's targets: {calories} kcal, {protein_g}g protein, {fat_g}g fat, {carbs_g}g carbs
- Current weight: {weight_kg} kg
- Days tracking: {days_tracking}
- Yesterday's intake: {yesterday_calories} kcal, {yesterday_protein}g protein

Write a brief, personalized morning coaching message. Reference their specific data.
Be warm and motivating. 2-3 sentences max."""

EVENING_CHECK_TEMPLATE = """User profile:
- Name: {name}
- Goal: {goal_type}
- Today's targets: {calories} kcal, {protein_g}g protein
- Consumed so far: {consumed_calories} kcal, {consumed_protein}g protein
- Remaining: {remaining_calories} kcal, {remaining_protein}g protein
- Time: evening

Write a brief evening check-in message. If they have significant remaining macros,
suggest what to eat. If they're close to goal, encourage them to finish strong.
2-3 sentences max. Be specific about what food would help if they're under protein."""

WEEKLY_SUMMARY_TEMPLATE = """User's weekly nutrition data:
- Name: {name}
- Goal: {goal_type} ({intensity})
- Calorie target: {calorie_target} kcal/day
- Week averages: {avg_calories} kcal, {avg_protein}g protein, {avg_fat}g fat, {avg_carbs}g carbs
- Days logged: {days_logged}/7
- Weight change this week: {weight_change} kg
- Issues identified: {issues}

Write a personalized weekly summary. Be specific about what went well and what to improve.
Reference actual numbers. Keep it under 100 words. End with one actionable tip for next week."""

WEIGHT_ASSESSMENT_TEMPLATE = """User data:
- Goal: {goal_type} ({intensity})
- Expected weekly change: {expected_change} kg/week
- Actual weekly change: {actual_change} kg/week
- Duration tracking: {weeks} weeks

Assess if their progress is on track. If too fast (>1 kg/week loss), warn about muscle loss.
If too slow or wrong direction, provide insight. Be empathetic and constructive. 2-3 sentences."""
