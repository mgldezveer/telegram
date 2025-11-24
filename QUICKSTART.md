# Быстрый старт

## За 5 минут до первого поста

### 1. Получите токены

#### Telegram Bot Token
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям и получите токен
4. Сохраните токен - он понадобится

#### AI Provider API Key

**Option A: Groq (Recommended - Free tier available)**
1. Зарегистрируйтесь на [console.groq.com](https://console.groq.com)
2. Перейдите в API Keys
3. Создайте новый ключ
4. Сохраните ключ

**Option B: OpenAI**
1. Зарегистрируйтесь на [platform.openai.com](https://platform.openai.com)
2. Перейдите в API Keys
3. Создайте новый ключ
4. Сохраните ключ

#### Ваш Telegram ID
1. Откройте [@userinfobot](https://t.me/userinfobot)
2. Отправьте `/start`
3. Скопируйте ваш ID

### 2. Установка

```bash
# Клонируйте репозиторий
git clone https://github.com/mgldezveer/telegram.git
cd telegram

# Создайте .env файл
cp .env.example .env
```

### 3. Настройка

Откройте `.env` и заполните обязательные параметры:

```bash
# Обязательные параметры
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id

# Выберите один AI провайдер (обязательно):
GROQ_API_KEY=ваш_ключ_Groq
# ИЛИ
OPENAI_API_KEY=ваш_ключ_OpenAI

# Опциональные параметры (можно оставить по умолчанию)
AI_MODEL=qwen-2.5-72b-instruct
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=1000
DATABASE_URL=sqlite:///bot.db
REDIS_URL=redis://localhost:6379/0
DEFAULT_POSTING_FREQUENCY=3
LOG_LEVEL=INFO
```

### 4. Запуск

```bash
# С Docker (рекомендуется)
docker-compose up -d

# Или локально
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python run.py
```

### 5. Первый пост

1. Откройте Telegram и найдите вашего бота
2. Отправьте `/start`
3. Добавьте бота в ваш канал как администратора
4. Отправьте боту:
   ```
   /register -1001234567890 "Мой канал"
   ```
   (замените ID на ID вашего канала)

5. Сгенерируйте первый пост:
   ```
   /generate 1 технологии
   ```

🎉 Готово! Бот сгенерировал ваш первый пост!

## Что дальше?

### Настройте автоматическую публикацию

```bash
# Установите частоту публикаций (3 поста в день)
/config frequency 3

# Установите тему контента
/theme искусственный интеллект
```

### Проверьте статус

```bash
/status
```

### Просмотрите метрики

Откройте в браузере:
- Health check: http://localhost:9090/health
- Метрики: http://localhost:9090/metrics

## Частые вопросы

**Q: Как узнать ID моего канала?**

A: Добавьте [@userinfobot](https://t.me/userinfobot) в канал и он покажет ID

**Q: Бот не отвечает**

A: Проверьте:
1. Правильность токена в `.env`
2. Логи: `docker-compose logs bot`
3. Что бот запущен: `docker-compose ps`

**Q: Как изменить стиль постов?**

A: Отредактируйте настройки канала в базе данных или используйте команды конфигурации

**Q: Сколько стоит использование?**

A: Зависит от выбранного AI провайдера:
- Groq: Бесплатный tier доступен, очень низкая стоимость
- OpenAI: Примерно $0.01-0.03 за пост с GPT-4

## Полезные команды

```bash
# Просмотр логов
docker-compose logs -f bot

# Перезапуск
docker-compose restart bot

# Остановка
docker-compose down

# Обновление
git pull && docker-compose up -d --build
```

## Следующие шаги

1. Прочитайте [README.md](README.md) для полной документации
2. Изучите [DEPLOYMENT.md](DEPLOYMENT.md) для production развертывания
3. Настройте мониторинг и алерты
4. Добавьте больше каналов

## Поддержка

Нужна помощь? Создайте issue на GitHub!
