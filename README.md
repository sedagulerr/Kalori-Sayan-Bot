# 🍽️ Calorie Counter Telegram Bot

A Telegram bot that turns a free-text meal description ("200g chicken
breast, 1 cup rice, split between 4 people") into a structured calorie and
macro breakdown, powered by the Claude API.

Built as a hands-on project to practice integrating an LLM into a real
application — with a deliberate focus on **separating AI-generated data
from deterministic business logic**, **structured output validation**, and
**test coverage**.

## What it does

```
You:  200g chicken breast, 1 cup cooked rice, split between 4 people
Bot:  📋 Ingredients:
      • Chicken breast (200g): 330 kcal
      • Rice, cooked (1 cup / 180g): 206 kcal

      Total: 536 kcal | 66.3g protein / 45.0g carbs / 7.3g fat

      👥 Split between 4:
      🔥 134 kcal/person
      🥩 16.6g protein
      🍞 11.2g carbs
      🧈 1.8g fat

You:  değerlendir  (assess this meal)
Bot:  [shows meal-type buttons: Breakfast / Lunch / Dinner / Snack]
You:  [taps Lunch]
Bot:  This meal is protein-rich and balanced for a lunch...
```

It also keeps a running daily log (SQLite) accessible via a **📅 Today's
Total** button or the `/bugun` command.

## Why this project

I'm a QA/test engineer and data analyst candidate learning how to ship a
small AI-integrated product end to end. This project was a way to practice
— and demonstrate — a few things that matter in production AI systems:

- **AI does extraction, code does math.** The LLM never calculates totals
  or per-person splits — it only extracts structured ingredient data. All
  arithmetic lives in pure, unit-tested Python functions
  (`calculations.py`). This keeps results deterministic and testable,
  and is a deliberate architectural boundary rather than an accident.
- **Structured output over free text.** Ingredient extraction uses
  Claude's tool-use (function calling) with a strict JSON schema, instead
  of asking the model to "reply in JSON" — far fewer parsing failures.
- **Prompt hardening against hallucination.** Early testing showed the
  model would sometimes invent ingredients for unrelated messages (e.g.
  "hi") or default an unspecified portion count to `1` instead of asking.
  Both were caught through manual testing and fixed by tightening the
  tool schema and prompt instructions — a small but concrete example of
  treating LLM output like any other unreliable external input that needs
  validation.
- **Test coverage on the parts that can be tested.** The calculation and
  database layers are pure functions with no external dependencies, so
  they're covered by 10 pytest unit tests (edge cases: empty input, zero/
  negative portion counts, multi-user data isolation).

## Tech stack

- Python, [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Anthropic API](https://docs.anthropic.com) (Claude, tool use for structured output)
- SQLite (daily history)
- pytest (unit tests)

## Architecture

```
main.py            Telegram handlers, conversation state, orchestration
claude_service.py  Claude API calls (ingredient parsing + meal assessment)
calculations.py    Pure functions: totals, per-portion math (no AI, fully tested)
db.py              SQLite layer for daily history (fully tested)
test_*.py          10 pytest unit tests
```

## Setup

### 1. Get a Telegram bot token
Message **@BotFather** on Telegram, send `/newbot`, follow the prompts,
and copy the token it gives you.

### 2. Get an Anthropic API key
Create one at [console.anthropic.com](https://console.anthropic.com).
Cost is usage-based (pay-as-you-go); this project uses the Haiku model,
so typical development/testing usage costs well under $1.

### 3. Install

```bash
git clone https://github.com/sedagulerr/Kalori-Sayan-Bot.git
cd Kalori-Sayan-Bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env           # then fill in your token/key
```

### 4. Run tests (optional but recommended)

```bash
pytest -v
```

### 5. Run the bot

```bash
python main.py
```

Message your bot on Telegram, send `/start`, and try a meal description.

## Possible next steps

- Deploy to Render/Fly.io (swap `run_polling()` for a webhook)
- Rate limiting and friendlier error messages on API failures
- Weekly/monthly history views on top of the existing SQLite layer

---

🇹🇷 Türkçe kurulum talimatları için [README.tr.md](README.tr.md) dosyasına bakabilirsiniz.
