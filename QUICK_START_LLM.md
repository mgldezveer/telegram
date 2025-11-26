# 🚀 Быстрый старт LLM Integration

## За 5 минут до работающей системы!

### Шаг 1: Установка зависимостей (1 мин)

```bash
pip install groq google-generativeai huggingface_hub prometheus-client aiohttp
```

### Шаг 2: Получение API ключей (2 мин)

**Groq (рекомендуется):**
1. Откройте [console.groq.com](https://console.groq.com)
2. Зарегистрируйтесь
3. Создайте API Key
4. Скопируйте ключ

**Gemini (опционально):**
1. Откройте [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Войдите с Google
3. Создайте API Key
4. Скопируйте ключ

### Шаг 3: Настройка .env (1 мин)

Откройте `.env` и добавьте:

```env
# Groq (обязательно)
LLM_GROQ_ENABLED=true
GROQ_API_KEY=ваш_ключ_groq

# Gemini (опционально)
LLM_GEMINI_ENABLED=false
GEMINI_API_KEY=ваш_ключ_gemini

# Настройки
LLM_DEFAULT_PROVIDER=groq
LLM_FALLBACK_ENABLED=true
LLM_CACHE_ENABLED=true
```

### Шаг 4: Проверка (30 сек)

```bash
python -m src.llm.status_checker
```

Должно показать:
```
✅ groq: Available (0.5s)
```

### Шаг 5: Запуск! (30 сек)

```bash
python vibe_coding_bot.py
```

## ✅ Готово!

Теперь в Telegram боте доступны команды:

- `/vibe` - Генерация контента с реальным AI
- `/llm_status` - Проверка статуса (только админ)
- `/llm_stats` - Статистика (только админ)

## 📊 Опционально: Dashboard

Запустите web dashboard для мониторинга:

```bash
python -m src.llm.dashboard
```

Откройте: http://localhost:8080/dashboard

---

## 🆘 Проблемы?

**"No LLM providers enabled"**
→ Проверьте что `LLM_GROQ_ENABLED=true` и `GROQ_API_KEY` установлен

**"Invalid API key"**
→ Проверьте правильность ключа на console.groq.com

**"Rate limit exceeded"**
→ Включите fallback: `LLM_FALLBACK_ENABLED=true`

---

## 📚 Полная документация

См. `docs/LLM_INTEGRATION.md` для подробностей.

**Успехов!** 🎉
