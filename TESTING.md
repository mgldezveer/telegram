# Testing Guide

## Quick Test

### Lightweight Bot Test (Fastest)

Use the simple test script to verify bot connectivity:

```bash
python test_bot.py
```

This minimal test:
- ✅ Verifies bot token is valid
- ✅ Tests Telegram API connection
- ✅ Confirms message receiving works
- ✅ No database or services required

Test commands in Telegram:
- `/start` - Should reply "✅ Bot is working!"
- `/test` - Should reply "✅ Test successful!"

### Full System Test

Самый быстрый способ проверить что всё работает:

```bash
# 1. Проверка установки
python check_setup.py

# 2. Инициализация БД
python init_db.py

# 3. Запуск полного бота
python run.py
```

## Manual Testing Checklist

### 1. Bot Commands

В Telegram отправьте боту:

```
/start
```
✅ Ожидается: Приветственное сообщение

```
/help
```
✅ Ожидается: Список всех команд

```
/status
```
✅ Ожидается: Статус бота (uptime, версия, и т.д.)

### 2. Channel Management

```
/add_channel @your_test_channel tech
```
✅ Ожидается: Канал добавлен с категорией "tech"

```
/list_channels
```
✅ Ожидается: Список каналов с ID и категориями

### 3. Content Generation

```
/generate tech "Artificial Intelligence trends 2024"
```
✅ Ожидается: 
- Сообщение "Generating content..."
- Через несколько секунд - сгенерированный пост
- Пост должен быть на английском
- Должны быть хэштеги

```
/generate tech "Тренды искусственного интеллекта 2024"
```
✅ Ожидается:
- Пост на русском языке
- Релевантный контент по теме

### 4. Post Scheduling

```
/schedule 1 15:30
```
✅ Ожидается: Пост запланирован на 15:30 сегодня

```
/schedule 1 tomorrow 10:00
```
✅ Ожидается: Пост запланирован на 10:00 завтра

### 5. Analytics

```
/analytics 1
```
✅ Ожидается: Статистика канала (views, engagement, и т.д.)

## Testing Content Quality

### Test 1: Topic Relevance
```
/generate tech "quantum computing"
```
✅ Проверьте:
- Контент действительно о квантовых вычислениях
- Нет off-topic информации
- Факты выглядят правдоподобно

### Test 2: Language Detection
```
/generate tech "машинное обучение"
```
✅ Проверьте:
- Ответ на русском языке
- Правильная грамматика
- Хэштеги на русском

### Test 3: Content Length
```
/generate tech "AI"
```
✅ Проверьте:
- Длина поста разумная (не слишком короткий/длинный)
- Есть структура (параграфы)
- Есть хэштеги

### Test 4: Hashtag Generation
✅ Проверьте в любом сгенерированном посте:
- Есть 3-5 хэштегов
- Хэштеги релевантны теме
- Хэштеги на том же языке что и пост

## Testing Error Handling

### Test 1: Invalid Channel
```
/add_channel @nonexistent_channel_12345 tech
```
✅ Ожидается: Понятное сообщение об ошибке

### Test 2: Invalid Time Format
```
/schedule 1 25:00
```
✅ Ожидается: Сообщение о неправильном формате времени

### Test 3: Non-existent Post
```
/schedule 999 14:00
```
✅ Ожидается: Сообщение что пост не найден

### Test 4: AI API Failure
Временно установите неправильный GROQ_API_KEY в .env и перезапустите:
```
/generate tech "test"
```
✅ Ожидается: Понятное сообщение об ошибке (не технические детали)

## Performance Testing

### Test 1: Multiple Requests
Отправьте 5 команд `/generate` подряд:
```
/generate tech "AI"
/generate tech "ML"
/generate tech "DL"
/generate tech "NLP"
/generate tech "CV"
```
✅ Проверьте:
- Все запросы обработаны
- Нет зависаний
- Ответы приходят в разумное время (< 30 сек каждый)

### Test 2: Concurrent Users
Попросите друга также отправить команды боту одновременно с вами.
✅ Проверьте:
- Оба получают ответы
- Нет перемешивания ответов
- Нет ошибок

## Database Testing

### Check Database
```bash
# Для SQLite
sqlite3 bot.db "SELECT * FROM channels;"
sqlite3 bot.db "SELECT * FROM posts;"
sqlite3 bot.db "SELECT * FROM metrics;"
```

✅ Проверьте:
- Данные сохраняются корректно
- Нет дублирования
- Связи между таблицами работают

## Monitoring Testing

### Check Health Endpoint
```bash
curl http://localhost:9090/health
```
✅ Ожидается: `{"status": "healthy", ...}`

### Check Metrics
```bash
curl http://localhost:9090/metrics
```
✅ Ожидается: Prometheus метрики

## Integration Testing

### Full Workflow Test
1. Добавьте канал: `/add_channel @test tech`
2. Сгенерируйте контент: `/generate tech "test topic"`
3. Запланируйте пост: `/schedule 1 +5min`
4. Подождите 5 минут
5. Проверьте что пост опубликован в канале
6. Проверьте аналитику: `/analytics 1`

✅ Весь процесс должен работать без ошибок

## Test Scripts

### test_bot.py - Simple Connectivity Test

Quick verification script that tests basic bot functionality:

```bash
python test_bot.py
```

**What it tests:**
- Bot token validity
- Telegram API connection
- Command handlers registration
- Message receiving/sending

**Use when:**
- First time setup
- Debugging connection issues
- Quick smoke test
- CI/CD pipeline checks

### run.py - Full Bot Test

Complete bot with all services:

```bash
python run.py
```

**What it tests:**
- All bot services
- Database connectivity
- AI integration
- Full command set

## Automated Tests

Если вы хотите запустить автоматические тесты:

```bash
# Установите pytest
pip install pytest pytest-asyncio

# Запустите тесты
pytest tests/ -v

# С покрытием кода
pytest tests/ --cov=src --cov-report=html
```

## Common Issues

### Issue: Bot doesn't respond
**Solution**: 
- Run quick test first: `python test_bot.py`
- Check bot is running: `ps aux | grep python`
- Check logs for errors
- Verify TELEGRAM_BOT_TOKEN

### Issue: AI generation fails
**Solution**:
- Check GROQ_API_KEY is valid
- Check Groq API status
- Try with simpler topic

### Issue: Posts not publishing
**Solution**:
- Verify bot is admin in channel
- Check channel ID is correct
- Check bot has posting permissions

### Issue: Database errors
**Solution**:
- Reinitialize: `python init_db.py`
- Check file permissions
- Check disk space

## Test Results Template

```
Date: ___________
Tester: ___________

Bot Commands:        [ ] Pass  [ ] Fail
Channel Management:  [ ] Pass  [ ] Fail
Content Generation:  [ ] Pass  [ ] Fail
Post Scheduling:     [ ] Pass  [ ] Fail
Analytics:           [ ] Pass  [ ] Fail
Error Handling:      [ ] Pass  [ ] Fail
Performance:         [ ] Pass  [ ] Fail

Notes:
_________________________________
_________________________________
_________________________________
```

## Next Steps

После успешного тестирования:
1. Настройте автоматическое планирование
2. Добавьте реальные каналы
3. Настройте темы контента
4. Запустите в production (см. DEPLOYMENT.md)
