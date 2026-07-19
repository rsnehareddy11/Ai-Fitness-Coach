# CoachLine — Personalized Diet & Workout Plan Generator

A small Flask website that takes someone's stats (age, sex, weight, height,
activity level, goal, diet preference) and generates:

- Macro targets (protein / carbs / fat, in grams)
- A sample daily meal plan matched to their diet preference
- A full weekly training split matched to their goal and available days

## Run it

```bash
pip install flask
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## How the numbers are calculated

- **BMR**: Mifflin-St Jeor equation
- **TDEE**: BMR × activity multiplier (1.2 – 1.725)
- **Calorie target**: TDEE adjusted for goal
  (weight loss −20%, muscle gain +12%, athletic performance +10%,
  general fitness unchanged), with a safety floor (1500 kcal men / 1200 kcal women)
- **Macros**: goal-specific protein/carb/fat split, with a protein floor of
  1.6–2.0 g per kg bodyweight
- **Training days/week**: 3–6, based on current activity level
- **Split type**: full-body + HIIT (weight loss), push/pull/legs (muscle gain),
  plyometrics + conditioning (athletic performance), or balanced full-body +
  cardio + mobility (general fitness)

## Project structure

```
fitcoach/
├── app.py                  # Flask app: calculations + plan generators + routes
├── templates/
│   └── index.html          # Form + results page
├── static/
│   ├── css/style.css       # "Training log" visual design
│   └── js/main.js          # Form submit, fetch, render results
└── README.md
```

## Disclaimer

This tool gives general fitness estimates, not medical advice. Anyone with
health conditions should consult a doctor or registered dietitian before
starting a new diet or exercise program.
#
