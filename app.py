"""
CoachLine — a personalized diet & workout plan generator.
Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)

# --------------------------------------------------------------------------
# 1. CORE CALCULATIONS
# --------------------------------------------------------------------------

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very_active": 1.725,
}

ACTIVITY_DAYS = {
    "sedentary": 3,
    "light": 4,
    "moderate": 5,
    "very_active": 6,
}

GOAL_CALORIE_ADJUST = {
    "weight_loss": -0.20,
    "muscle_gain": 0.12,
    "general_fitness": 0.0,
    "athletic_performance": 0.10,
}

GOAL_MACROS = {  # protein / carbs / fat as fraction of total calories
    "weight_loss": (0.35, 0.35, 0.30),
    "muscle_gain": (0.30, 0.45, 0.25),
    "general_fitness": (0.25, 0.45, 0.30),
    "athletic_performance": (0.25, 0.50, 0.25),
}


def calc_bmr(gender, weight_kg, height_cm, age):
    """Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender == "male" else base - 161


def calc_plan_numbers(gender, weight_kg, height_cm, age, activity, goal):
    bmr = calc_bmr(gender, weight_kg, height_cm, age)
    tdee = bmr * ACTIVITY_MULTIPLIERS[activity]
    calories = tdee * (1 + GOAL_CALORIE_ADJUST[goal])

    # Safety floors so calorie targets never drop dangerously low
    floor = 1500 if gender == "male" else 1200
    calories = max(calories, floor)

    p_pct, c_pct, f_pct = GOAL_MACROS[goal]
    protein_g = (calories * p_pct) / 4
    carbs_g = (calories * c_pct) / 4
    fat_g = (calories * f_pct) / 9

    # Protein floor tied to bodyweight for strength/fat-loss goals
    min_protein = weight_kg * (2.0 if goal in ("weight_loss", "muscle_gain") else 1.6)
    if protein_g < min_protein:
        protein_g = min_protein

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "calories": round(calories),
        "protein_g": round(protein_g),
        "carbs_g": round(carbs_g),
        "fat_g": round(fat_g),
    }


# --------------------------------------------------------------------------
# 2. DIET PLAN GENERATOR
# --------------------------------------------------------------------------

FOOD_LIBRARY = {
    "non_veg": {
        "breakfast": [
            "3 whole eggs + 1 slice whole-grain toast + avocado",
            "Greek yogurt with berries, honey & granola",
            "Egg white omelette with spinach, mushroom & feta",
            "Oats cooked in milk with banana & peanut butter",
        ],
        "lunch": [
            "Grilled chicken breast, brown rice & steamed broccoli",
            "Tuna salad with mixed greens, chickpeas & olive oil",
            "Turkey & quinoa bowl with roasted vegetables",
            "Salmon fillet with sweet potato & asparagus",
        ],
        "dinner": [
            "Baked fish with sautéed greens & wild rice",
            "Lean beef stir-fry with mixed vegetables & noodles",
            "Grilled chicken thighs with roasted potatoes & salad",
            "Shrimp & vegetable skillet with quinoa",
        ],
        "snacks": [
            "Boiled eggs (2) + a handful of almonds",
            "Cottage cheese with pineapple chunks",
            "Protein shake with a banana",
            "Beef jerky & baby carrots",
        ],
    },
    "vegetarian": {
        "breakfast": [
            "Greek yogurt parfait with granola & mixed berries",
            "Paneer bhurji with whole-wheat paratha",
            "Vegetable omelette with cheese & toast",
            "Oats with milk, chia seeds & fruit",
        ],
        "lunch": [
            "Rajma (kidney beans) with brown rice & salad",
            "Paneer tikka bowl with quinoa & roasted veggies",
            "Lentil soup with whole-grain bread & side salad",
            "Chickpea & feta grain bowl with olive oil dressing",
        ],
        "dinner": [
            "Tofu stir-fry with mixed vegetables & rice",
            "Palak paneer with brown rice",
            "Vegetable & bean chili with a side of yogurt",
            "Stuffed bell peppers with quinoa & cheese",
        ],
        "snacks": [
            "Greek yogurt with honey & walnuts",
            "Roasted chickpeas & a piece of fruit",
            "Cottage cheese with cucumber sticks",
            "Protein shake (whey) with a handful of nuts",
        ],
    },
    "vegan": {
        "breakfast": [
            "Overnight oats with almond milk, chia & berries",
            "Tofu scramble with spinach & whole-grain toast",
            "Smoothie: banana, spinach, plant protein & peanut butter",
            "Chickpea flour pancakes with fruit compote",
        ],
        "lunch": [
            "Buddha bowl: quinoa, chickpeas, roasted veg & tahini",
            "Lentil & vegetable curry with brown rice",
            "Black bean & corn salad with avocado",
            "Tempeh stir-fry with brown rice & broccoli",
        ],
        "dinner": [
            "Chana masala with brown rice",
            "Tofu & vegetable stir-fry with soba noodles",
            "Three-bean chili with a side salad",
            "Stuffed sweet potato with black beans & salsa",
        ],
        "snacks": [
            "Hummus with carrot & celery sticks",
            "Plant-based protein shake with berries",
            "Trail mix (nuts, seeds & dried fruit)",
            "Edamame with sea salt",
        ],
    },
}

DIET_TIPS = {
    "weight_loss": "Prioritize protein & fiber to stay full on fewer calories. Drink water before meals and limit liquid calories.",
    "muscle_gain": "Eat in a steady surplus, hit your protein target daily, and don't skip carbs around workouts — they fuel recovery.",
    "general_fitness": "Focus on whole foods, colorful vegetables, and consistent meal timing rather than perfection.",
    "athletic_performance": "Time carbs around training sessions for energy and recovery; hydrate well before/after workouts.",
}


def generate_diet_plan(diet_pref, numbers, goal):
    lib = FOOD_LIBRARY[diet_pref]
    plan = {
        "breakfast": random.choice(lib["breakfast"]),
        "lunch": random.choice(lib["lunch"]),
        "dinner": random.choice(lib["dinner"]),
        "snack": random.choice(lib["snacks"]),
        "tip": DIET_TIPS[goal],
    }
    return plan


# --------------------------------------------------------------------------
# 3. WORKOUT PLAN GENERATOR
# --------------------------------------------------------------------------

EXERCISE_POOLS = {
    "push": ["Push-ups", "Barbell bench press", "Overhead dumbbell press", "Incline dumbbell press", "Triceps dips"],
    "pull": ["Pull-ups / lat pulldown", "Bent-over rows", "Seated cable rows", "Face pulls", "Bicep curls"],
    "legs": ["Back squats", "Romanian deadlifts", "Walking lunges", "Leg press", "Calf raises"],
    "full_body": ["Goblet squats", "Push-ups", "Dumbbell rows", "Kettlebell swings", "Plank"],
    "cardio": ["Brisk incline walk", "Cycling intervals", "Jump rope", "Rowing machine", "Stair climber"],
    "hiit": ["Burpees", "Mountain climbers", "Jump squats", "High knees", "Battle ropes"],
    "mobility": ["Dynamic stretching flow", "Hip openers", "Foam rolling", "Yoga flow", "Shoulder mobility drills"],
    "plyo": ["Box jumps", "Broad jumps", "Lateral bounds", "Med-ball slams", "Sprint intervals"],
}

GOAL_REP_SCHEME = {
    "weight_loss": "3 sets x 15 reps (short 30s rest)",
    "muscle_gain": "4 sets x 8-10 reps (60-90s rest)",
    "general_fitness": "3 sets x 12 reps (45s rest)",
    "athletic_performance": "4 sets x 6-8 reps, explosive tempo (90s rest)",
}


def build_day(category, goal, n=5):
    pool = EXERCISE_POOLS[category]
    picks = random.sample(pool, min(n, len(pool)))
    scheme = GOAL_REP_SCHEME[goal]
    return [{"exercise": ex, "scheme": scheme} for ex in picks]


def generate_workout_plan(goal, activity):
    days_per_week = ACTIVITY_DAYS[activity]

    if goal == "weight_loss":
        templates = ["full_body", "hiit", "full_body", "cardio", "full_body", "hiit"]
    elif goal == "muscle_gain":
        templates = ["push", "pull", "legs", "push", "pull", "legs"]
    elif goal == "athletic_performance":
        templates = ["plyo", "full_body", "cardio", "legs", "plyo", "full_body"]
    else:  # general_fitness
        templates = ["full_body", "cardio", "full_body", "mobility", "full_body", "cardio"]

    week = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    template_idx = 0
    for i, day_name in enumerate(day_names):
        if i < days_per_week:
            category = templates[template_idx % len(templates)]
            template_idx += 1
            week.append({
                "day": day_name,
                "focus": category.replace("_", " ").title(),
                "exercises": build_day(category, goal),
                "rest": False,
            })
        else:
            week.append({"day": day_name, "focus": "Rest / Mobility", "exercises": [], "rest": True})

    return week


# --------------------------------------------------------------------------
# 4. ROUTES
# --------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/plan", methods=["POST"])
def api_plan():
    data = request.get_json(force=True)

    try:
        gender = data["gender"]
        age = float(data["age"])
        weight_kg = float(data["weight"])
        height_cm = float(data["height"])
        activity = data["activity"]
        goal = data["goal"]
        diet_pref = data["diet"]

        if age <= 0 or weight_kg <= 0 or height_cm <= 0:
            raise ValueError("Values must be positive")
        if activity not in ACTIVITY_MULTIPLIERS or goal not in GOAL_MACROS or diet_pref not in FOOD_LIBRARY:
            raise ValueError("Invalid option")
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    numbers = calc_plan_numbers(gender, weight_kg, height_cm, age, activity, goal)
    diet_plan = generate_diet_plan(diet_pref, numbers, goal)
    workout_plan = generate_workout_plan(goal, activity)

    return jsonify({
        "numbers": numbers,
        "diet": diet_plan,
        "workout": workout_plan,
        "days_per_week": ACTIVITY_DAYS[activity],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
