# 🤖 LLM Integration Guide

Полное руководство по интеграции бесплатных LLM провайдеров в AI Content Bot.

## 📋 Содержание

- [Обзор](#обзор)
- [Поддерживаемые провайдеры](#поддерживаемые-провайдеры)
- [Быстрый старт](#быстрый-старт)
- [Получение API ключей](#получение-api-ключей)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [Мониторинг](#мониторинг)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Обзор

LLM Integration предоставляет единый интерфейс для работы с несколькими бесплатными LLM провайдерами:

**Ключевые возможности:**
- ✅ **3 бесплатных провайдера** (Groq, Gemini, Hugging Face)
- ✅ **Автоматический fallback** при ошибках
- ✅ **Кэширование ответов** для экономии запросов
- ✅ **Rate limiting** для соблюдения лимитов
- ✅ **Retry логика** с exponential backoff
- ✅ **Мониторинг и метрики** (Prometheus)
- ✅ **Web dashboard** для просмотра статистики

---

## 🔌 Поддерживаемые провайдеры

### 1. Groq (Рекомендуется)

**Преимущества:**
- ⚡ Очень быстрая генерация (< 1 секунды)
- 🆓 Бесплатный tier: 30 запросов/минуту
- 🎯 Модели: Llama 3.3 70B, Mixtral 8x7B

**Лимиты:**
- 30 requests/minute
- 14,400 requests/day

### 2. Google Gemini

**Преимущества:**
- 🎨 Высокое качество генерации
- 🆓 Бесплатный tier: 60 запросов/минуту
- 🛡️ Встроенные safety settings

**Лимиты:**
- 60 requests/minute
- 1,500 requests/day

### 3. Hugging Face

**Преимущества:**
- 🔄 Множество моделей с автоматическим fallback
- 🆓 Бесплатный Inference API
- 📚 Большой выбор моделей

**Лимиты:**
- 10 requests/minute
- 1,000 requests/day

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install groq google-generativeai huggingface_hub
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте API ключи:

```env
# Groq (рекомендуется)
LLM_GROQ_ENABLED=true
GROQ_API_KEY=your_groq_api_key_here

# Gemini (опционально)
LLM_GEMINI_ENABLED=false
GEMINI_API_KEY=your_gemini_api_key_here

# Hugging Face (опционально)
LLM_HF_ENABLED=false
HF_API_KEY=your_hf_api_key_here
```

### 3. Проверка статуса

```bash
python -m src.llm.status_checker
```

### 4. Запуск бота

```bash
python vibe_coding_bot.py
```

---

## 🔑 Получение API ключей

### Groq API Key

1. Перейдите на [console.groq.com](https://console.groq.com)
2. Зарегистрируйтесь или войдите
3. Перейдите в раздел "API Keys"
4. Нажмите "Create API Key"
5. Скопируйте ключ и добавьте в `.env`

**Лимиты бесплатного tier:**
- 30 requests/minute
- 14,400 requests/day
- Модели: Llama 3.3 70B, Mixtral 8x7B

### Google Gemini API Key

1. Перейдите на [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Войдите с Google аккаунтом
3. Нажмите "Create API Key"
4. Скопируйте ключ и добавьте в `.env`

**Лимиты бесплатного tier:**
- 60 requests/minute
- 1,500 requests/day
- Модель: Gemini 1.5 Flash

### Hugging Face API Token

1. Перейдите на [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Зарегистрируйтесь или войдите
3. Нажмите "New token"
4. Выберите "Read" permissions
5. Скопируйте токен и добавьте в `.env`

**Лимиты бесплатного tier:**
- 10 requests/minute
- 1,000 requests/day
- Доступ к бесплатным моделям

---

## ⚙️ Конфигурация

### Основные настройки

```env
# Default провайдер
LLM_DEFAULT_PROVIDER=groq

# Автоматический fallback
LLM_FALLBACK_ENABLED=true

# Кэширование
LLM_CACHE_ENABLED=true
LLM_CACHE_TTL=3600          # 1 час
LLM_CACHE_MAX_SIZE=1000

# Rate limiting
LLM_RATE_LIMIT_ENABLED=true

# Retry настройки
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0

# Таймауты
LLM_REQUEST_TIMEOUT=30
```

### Приоритеты провайдеров

Установите приоритет для каждого провайдера (меньше = выше приоритет):

```env
LLM_GROQ_PRIORITY=1        # Первый выбор
LLM_GEMINI_PRIORITY=2      # Второй выбор
LLM_HF_PRIORITY=3          # Третий выбор
```

### Выбор моделей

```env
# Groq
GROQ_MODEL=llama-3.3-70b-versatile

# Gemini
GEMINI_MODEL=gemini-1.5-flash

# Hugging Face (оставьте пустым для автоматического выбора)
# HF_MODEL=
```

---

## 💻 Использование

### Базовое использование

```python
from src.llm.manager import LLMManager
from src.llm.config import get_config
from src.llm.providers import (
    create_groq_provider_from_env,
    create_gemini_provider_from_env
)

# Создание провайдеров
providers = []

groq = create_groq_provider_from_env()
if groq:
    providers.append(groq)

gemini = create_gemini_provider_from_env()
if gemini:
    providers.append(gemini)

# Создание менеджера
manager = LLMManager(providers=providers)

# Генерация текста
response = await manager.generate(
    prompt="Напиши короткий пост о Python",
    max_tokens=500,
    temperature=0.7
)

print(response.text)
```

### С кэшированием

```python
from src.llm.cache import CacheService

# Создание кэша
cache = CacheService(max_memory_size=1000, default_ttl=3600)

# Менеджер с кэшем
manager = LLMManager(
    providers=providers,
    cache_service=cache
)

# Первый запрос - идет к API
response1 = await manager.generate(prompt="Hello")

# Второй запрос - из кэша
response2 = await manager.generate(prompt="Hello")
```

### С rate limiting

```python
from src.llm.rate_limiter import RateLimitManager

# Создание rate limiter
rate_limiter = RateLimitManager()

# Менеджер с rate limiting
manager = LLMManager(
    providers=providers,
    rate_limiter=rate_limiter
)
```

---

## 📊 Мониторинг

### CLI команды (только для админов)

```bash
# Проверка статуса провайдеров
/llm_status

# Статистика использования
/llm_stats

# Переключение провайдера
/llm_switch groq

# Очистка кэша
/llm_cache_clear

# Перезагрузка конфигурации
/llm_reload
```

### Web Dashboard

Запустите dashboard для просмотра метрик:

```bash
python -m src.llm.dashboard
```

Откройте в браузере: `http://localhost:8080/dashboard`

**Доступные endpoints:**
- `/dashboard` - HTML dashboard
- `/health` - Health check
- `/api/stats` - JSON статистика
- `/api/status` - Статус провайдеров
- `/metrics` - Prometheus метрики

### Prometheus метрики

Если установлен `prometheus-client`, доступны метрики:

```
# Запросы
llm_requests_total{provider="groq", status="success"}
llm_requests_total{provider="groq", status="error"}

# Время отклика
llm_request_duration_seconds{provider="groq"}

# Кэш
llm_cache_hits_total
llm_cache_misses_total

# Rate limiting
llm_rate_limit_hits_total{provider="groq"}

# Токены
llm_tokens_used_total{provider="groq"}

# Активные провайдеры
llm_active_providers
```

---

## 🔧 Troubleshooting

### Проблема: "No LLM providers enabled"

**Решение:**
1. Проверьте `.env` файл
2. Убедитесь что хотя бы один провайдер включен:
   ```env
   LLM_GROQ_ENABLED=true
   GROQ_API_KEY=your_key_here
   ```
3. Перезапустите бота

### Проблема: "Invalid API key"

**Решение:**
1. Проверьте правильность API ключа
2. Убедитесь что ключ активен
3. Проверьте лимиты на сайте провайдера

### Проблема: "Rate limit exceeded"

**Решение:**
1. Включите fallback на другие провайдеры:
   ```env
   LLM_FALLBACK_ENABLED=true
   ```
2. Включите кэширование:
   ```env
   LLM_CACHE_ENABLED=true
   ```
3. Добавьте дополнительные провайдеры

### Проблема: "All providers failed"

**Решение:**
1. Проверьте статус провайдеров:
   ```bash
   python -m src.llm.status_checker
   ```
2. Проверьте интернет соединение
3. Проверьте логи на наличие ошибок
4. Убедитесь что API ключи валидны

### Проблема: Медленная генерация

**Решение:**
1. Используйте Groq (самый быстрый)
2. Включите кэширование
3. Уменьшите `max_tokens`
4. Проверьте сетевое соединение

---

## 📈 Оптимизация

### Экономия запросов

1. **Включите кэширование:**
   ```env
   LLM_CACHE_ENABLED=true
   LLM_CACHE_TTL=3600
   ```

2. **Используйте семантическое кэширование** для похожих запросов

3. **Оптимизируйте промпты** - короче = меньше токенов

### Повышение надежности

1. **Включите fallback:**
   ```env
   LLM_FALLBACK_ENABLED=true
   ```

2. **Настройте несколько провайдеров:**
   ```env
   LLM_GROQ_ENABLED=true
   LLM_GEMINI_ENABLED=true
   LLM_HF_ENABLED=true
   ```

3. **Увеличьте retry attempts:**
   ```env
   LLM_MAX_RETRIES=5
   ```

### Повышение скорости

1. **Используйте Groq** как primary провайдер
2. **Уменьшите timeout:**
   ```env
   LLM_REQUEST_TIMEOUT=15
   ```
3. **Используйте кэш** для повторяющихся запросов

---

## 🔗 Полезные ссылки

- [Groq Documentation](https://console.groq.com/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference)
- [Prometheus Metrics](https://prometheus.io/docs/introduction/overview/)

---

## 📝 Примеры использования

### Пример 1: Генерация контента для Telegram

```python
async def generate_telegram_post(theme: str):
    manager = get_llm_manager()
    
    response = await manager.generate(
        prompt=f"Создай короткий пост для Telegram на тему: {theme}",
        max_tokens=300,
        temperature=0.8,
        system_prompt="Ты - креативный копирайтер для Telegram каналов"
    )
    
    return response.text
```

### Пример 2: Обработка ошибок

```python
async def safe_generate(prompt: str):
    manager = get_llm_manager()
    
    try:
        response = await manager.generate(prompt=prompt)
        return response.text
    except RateLimitError:
        return "⚠️ Превышен лимит запросов. Попробуйте позже."
    except APIError as e:
        logger.error(f"API error: {e}")
        return "❌ Ошибка генерации. Попробуйте еще раз."
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "❌ Произошла ошибка."
```

### Пример 3: Batch обработка

```python
async def generate_multiple_posts(themes: list):
    manager = get_llm_manager()
    results = []
    
    for theme in themes:
        try:
            response = await manager.generate(
                prompt=f"Пост на тему: {theme}",
                max_tokens=200
            )
            results.append({
                'theme': theme,
                'text': response.text,
                'provider': response.provider
            })
        except Exception as e:
            logger.error(f"Failed for theme {theme}: {e}")
            results.append({
                'theme': theme,
                'text': None,
                'error': str(e)
            })
    
    return results
```

---

## 🎓 Best Practices

1. **Всегда используйте fallback** - не полагайтесь на один провайдер
2. **Включайте кэширование** - экономьте запросы и деньги
3. **Мониторьте метрики** - следите за использованием и ошибками
4. **Оптимизируйте промпты** - короче = быстрее и дешевле
5. **Обрабатывайте ошибки** - всегда имейте fallback логику
6. **Тестируйте локально** - проверяйте перед деплоем
7. **Следите за лимитами** - не превышайте rate limits

---

## 📞 Поддержка

Если у вас возникли проблемы:

1. Проверьте [Troubleshooting](#troubleshooting)
2. Посмотрите логи: `tail -f bot.log`
3. Проверьте статус: `/llm_status`
4. Создайте issue на GitHub

---

**Версия:** 1.0.0  
**Последнее обновление:** 2024
