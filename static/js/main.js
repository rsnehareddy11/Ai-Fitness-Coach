const form = document.getElementById('plan-form');
const results = document.getElementById('results');
const DIAL_CIRCUMFERENCE = 596.9; // 2 * PI * 95
const DIAL_MAX_KCAL = 4000; // visual scale ceiling

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const payload = {
    gender: document.getElementById('gender').value,
    age: document.getElementById('age').value,
    weight: document.getElementById('weight').value,
    height: document.getElementById('height').value,
    activity: document.getElementById('activity').value,
    goal: document.getElementById('goal').value,
    diet: document.getElementById('diet').value,
  };

  const btn = form.querySelector('.submit-btn');
  const originalText = btn.textContent;
  btn.textContent = 'Calculating…';
  btn.disabled = true;

  try {
    const res = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Something went wrong');
    }
    const data = await res.json();
    renderResults(data);
    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    alert('Could not generate plan: ' + err.message);
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
});

function renderResults(data) {
  const { numbers, diet, workout, days_per_week } = data;

  // --- dial ---
  document.getElementById('dial-calories').textContent = numbers.calories.toLocaleString();
  document.getElementById('stat-bmr').textContent = numbers.bmr.toLocaleString();
  document.getElementById('stat-tdee').textContent = numbers.tdee.toLocaleString();

  const fraction = Math.min(numbers.calories / DIAL_MAX_KCAL, 1);
  const offset = DIAL_CIRCUMFERENCE * (1 - fraction);
  const progressEl = document.getElementById('dial-progress');
  // reset then animate
  progressEl.style.transition = 'none';
  progressEl.style.strokeDashoffset = DIAL_CIRCUMFERENCE;
  requestAnimationFrame(() => {
    progressEl.style.transition = '';
    progressEl.style.strokeDashoffset = offset;
  });

  // --- macros ---
  const totalMacroCals = numbers.protein_g * 4 + numbers.carbs_g * 4 + numbers.fat_g * 9;
  setMacroBar('protein', numbers.protein_g, totalMacroCals * 0 + (numbers.protein_g * 4) / totalMacroCals);
  setMacroBar('carbs', numbers.carbs_g, (numbers.carbs_g * 4) / totalMacroCals);
  setMacroBar('fat', numbers.fat_g, (numbers.fat_g * 9) / totalMacroCals);

  // --- meals ---
  const mealGrid = document.getElementById('meal-grid');
  mealGrid.innerHTML = '';
  const meals = [
    ['01', 'Breakfast', diet.breakfast],
    ['02', 'Lunch', diet.lunch],
    ['03', 'Dinner', diet.dinner],
    ['04', 'Snack', diet.snack],
  ];
  meals.forEach(([idx, label, text]) => {
    const card = document.createElement('div');
    card.className = 'meal-card';
    card.setAttribute('data-index', idx);
    card.innerHTML = `<h4>${label}</h4><p>${text}</p>`;
    mealGrid.appendChild(card);
  });
  document.getElementById('diet-tip').textContent = diet.tip;

  // --- weekly training ---
  document.getElementById('days-per-week-note').textContent =
    `${days_per_week} training day${days_per_week === 1 ? '' : 's'} per week, matched to your activity level and goal.`;

  const weekStrip = document.getElementById('week-strip');
  weekStrip.innerHTML = '';
  workout.forEach((day) => {
    const card = document.createElement('div');
    card.className = 'day-card' + (day.rest ? ' rest' : '');
    if (day.rest) {
      card.innerHTML = `<div class="day-name">${day.day}</div><div class="day-focus">Rest</div>`;
    } else {
      const list = day.exercises
        .map((ex) => `<li><strong>${ex.exercise}</strong>${ex.scheme}</li>`)
        .join('');
      card.innerHTML = `
        <div class="day-name">${day.day}</div>
        <div class="day-focus">${day.focus}</div>
        <ul class="exercise-list">${list}</ul>
      `;
    }
    weekStrip.appendChild(card);
  });
}

function setMacroBar(key, grams, fraction) {
  document.getElementById(`bar-${key}`).style.width = `${Math.round(fraction * 100)}%`;
  document.getElementById(`val-${key}`).textContent = `${grams}g`;
}
