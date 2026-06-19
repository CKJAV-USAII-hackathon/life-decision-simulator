# 🧭 AI-консультант розвитку

Streamlit-додаток: чат на **Gemini** + збереження профілю користувача та
сценаріїв у **Supabase (Postgres)**.

## Швидкий старт

### 1. Залежності
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Створити Supabase-проєкт
1. Зайди на https://supabase.com → **New project** (запам'ятай пароль БД).
2. Коли проєкт готовий: **SQL Editor → New query** → встав вміст
   [`schema.sql`](schema.sql) → **Run**. Створяться таблиці `user_profiles`
   та `scenarios`, а також **вимкнеться RLS** (Row-Level Security), щоб
   `anon`-ключ міг писати без auth.
3. **Project Settings → API**: скопіюй **Project URL** і ключ
   (`anon public` достатньо для хакатону).

### 3. Ключ Gemini
Візьми на https://aistudio.google.com/apikey

### 4. Секрети
Скопіюй `.env.example` у `.env` і встав значення (без лапок і пробілів):
```
GEMINI_API_KEY=AIza...        # ключ Gemini завжди починається з "AIza"
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=...
```
> На Streamlit Community Cloud замість `.env` додай ті самі ключі в
> **Settings → Secrets** — код читає обидва джерела автоматично.

### 5. Запуск
```bash
streamlit run app.py
```

## Як користуватись
1. У боковій панелі введи **email** (це ідентифікатор користувача).
2. Вкладка **Профіль** — заповни анкету (колесо балансу, фокус, фактори),
   додай сценарії → **Зберегти**.
3. Вкладка **Чат** — консультант на Gemini бачить твій профіль і сценарії
   та відповідає в цьому контексті.

## Поведінка чату
Чат відповідає **коротко й чітко** (2–4 речення / до 4 пунктів), лише по темі
особистого розвитку, і відмовляється від сторонніх запитів. Налаштування —
у `llm.py`:
- `MODEL` — модель (`gemini-2.5-flash`, можна `gemini-2.5-pro`);
- `SYSTEM_BASE` — інструкції тону й формату;
- `temperature`, `max_output_tokens`, `thinking_config` — у виклику `chat()`.
- `thinking_budget=0` вимикає «мислення» моделі — без цього короткі відповіді
  обрізаються, бо thinking з'їдає `max_output_tokens`.

## Troubleshooting
- **`API key not valid`** — ключ Gemini неправильний. Має починатися з `AIza`
  (бери на https://aistudio.google.com/apikey).
- **`row violates row-level security policy`** — не вимкнено RLS. Виконай у
  Supabase SQL Editor:
  ```sql
  alter table user_profiles disable row level security;
  alter table scenarios disable row level security;
  ```
- **Порожні / обрізані відповіді чату** — переконайся, що в `chat()` є
  `thinking_config=types.ThinkingConfig(thinking_budget=0)`.

## Структура
| Файл | Призначення |
|------|-------------|
| `app.py` | Streamlit UI (анкета + чат) |
| `llm.py` | Обгортка Gemini (system prompt + контекст) |
| `db.py` | Supabase: save/load профілю та сценаріїв |
| `models.py` | `UserProfile`, `Scenario` |
| `config.py` | Читання секретів (st.secrets / .env) |
| `schema.sql` | Таблиці Supabase + вимкнення RLS |

## Що далі (поза поточним обсягом)
Скорингові формули (Goal Fit, Balance Score, Risk Penalty…), порівняння
сценаріїв, семантичний пошук — дивись дошку проєкту.
