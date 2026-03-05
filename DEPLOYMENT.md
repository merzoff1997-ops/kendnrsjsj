# 🌐 Руководство по развертыванию

Подробные инструкции по запуску MerAi & Monitoring на различных платформах.

---

## 📋 Содержание

- [BotHost for Telegram](#-bothost-for-telegram)
- [Heroku](#-heroku)
- [VPS (Linux)](#-vps-linux)
- [Railway](#-railway)
- [Replit](#-replit)
- [PythonAnywhere](#-pythonanywhere)
- [Локальный запуск](#-локальный-запуск)

---

## 🤖 BotHost for Telegram

**Рекомендуется для начинающих**

### Преимущества
- ✅ Простая настройка
- ✅ Бесплатный тариф
- ✅ Автоматический перезапуск
- ✅ Встроенные логи

### Инструкция

1. **Регистрация:**
   - Перейдите на [BotHost](https://bothost.app/)
   - Зарегистрируйтесь через Telegram

2. **Создание проекта:**
   - Нажмите "Создать бот"
   - Выберите "Python"

3. **Загрузка файлов:**
   ```
   Загрузите через веб-интерфейс:
   - merai_bot.py
   - requirements.txt
   ```

4. **Настройка переменных:**
   - Перейдите в "Настройки" → "Переменные окружения"
   - Добавьте:
     ```
     BOT_TOKEN=ваш_токен
     API_ID=ваш_api_id (опционально)
     API_HASH=ваш_api_hash (опционально)
     ```

5. **Запуск:**
   - Нажмите "Старт"
   - Проверьте логи на наличие ошибок

6. **Готово!** Бот запущен 24/7

---

## 🚀 Heroku

**Для продвинутых пользователей**

### Преимущества
- ✅ Надежная платформа
- ✅ Бесплатный тариф (550 часов/месяц)
- ✅ Git интеграция
- ✅ Легкое масштабирование

### Инструкция

1. **Установка Heroku CLI:**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku

   # Ubuntu/Debian
   curl https://cli-assets.heroku.com/install.sh | sh

   # Windows
   # Скачайте с https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Авторизация:**
   ```bash
   heroku login
   ```

3. **Создание приложения:**
   ```bash
   heroku create merai-monitoring-bot
   ```

4. **Настройка переменных:**
   ```bash
   heroku config:set BOT_TOKEN=ваш_токен
   heroku config:set API_ID=ваш_api_id
   heroku config:set API_HASH=ваш_api_hash
   ```

5. **Создание Procfile:**
   ```bash
   echo "worker: python merai_bot.py" > Procfile
   ```

6. **Деплой:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

7. **Запуск worker:**
   ```bash
   heroku ps:scale worker=1
   ```

8. **Проверка логов:**
   ```bash
   heroku logs --tail
   ```

---

## 🖥 VPS (Linux)

**Для опытных пользователей**

### Преимущества
- ✅ Полный контроль
- ✅ Высокая производительность
- ✅ Возможность кастомизации
- ✅ Не зависит от сторонних сервисов

### Требования
- Ubuntu 20.04+ или Debian 11+
- Python 3.12+
- Sudo права

### Инструкция

1. **Подключение к VPS:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Обновление системы:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Установка зависимостей:**
   ```bash
   sudo apt install python3.12 python3.12-venv python3-pip git -y
   ```

4. **Клонирование репозитория:**
   ```bash
   cd /opt
   sudo git clone https://github.com/ваш-username/merai-monitoring.git
   cd merai-monitoring
   ```

5. **Настройка окружения:**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Создание .env файла:**
   ```bash
   sudo nano .env
   ```
   Добавьте ваши данные и сохраните (Ctrl+X, Y, Enter)

7. **Создание systemd сервиса:**
   ```bash
   sudo nano /etc/systemd/system/merai.service
   ```

   Вставьте:
   ```ini
   [Unit]
   Description=MerAi Monitoring Bot
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/merai-monitoring
   Environment="PATH=/opt/merai-monitoring/venv/bin"
   ExecStart=/opt/merai-monitoring/venv/bin/python merai_bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

8. **Запуск сервиса:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable merai
   sudo systemctl start merai
   ```

9. **Проверка статуса:**
   ```bash
   sudo systemctl status merai
   ```

10. **Просмотр логов:**
    ```bash
    sudo journalctl -u merai -f
    ```

### Управление сервисом

```bash
# Остановить
sudo systemctl stop merai

# Перезапустить
sudo systemctl restart merai

# Отключить автозапуск
sudo systemctl disable merai

# Просмотреть логи
sudo journalctl -u merai --since today
```

---

## 🚂 Railway

**Современная альтернатива Heroku**

### Преимущества
- ✅ Простой интерфейс
- ✅ Автоматический деплой из GitHub
- ✅ Бесплатный тариф (500 часов/месяц)

### Инструкция

1. **Создание аккаунта:**
   - Перейдите на [Railway](https://railway.app/)
   - Войдите через GitHub

2. **Создание проекта:**
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий

3. **Настройка переменных:**
   - Перейдите в "Variables"
   - Добавьте:
     ```
     BOT_TOKEN
     API_ID
     API_HASH
     ```

4. **Готово!** Railway автоматически развернет проект

---

## 💻 Replit

**Для быстрого тестирования**

### Преимущества
- ✅ Онлайн IDE
- ✅ Не нужна установка
- ✅ Бесплатный тариф

### Инструкция

1. **Создание Repl:**
   - Перейдите на [Replit](https://replit.com/)
   - Нажмите "Create Repl"
   - Выберите "Python"

2. **Загрузка файлов:**
   - Загрузите `merai_bot.py` и `requirements.txt`

3. **Настройка Secrets:**
   - Откройте "Secrets" (иконка замка)
   - Добавьте:
     ```
     BOT_TOKEN=ваш_токен
     ```

4. **Изменение .replit файла:**
   ```toml
   run = "python merai_bot.py"
   ```

5. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Запуск:**
   - Нажмите "Run"

**Примечание:** Replit может засыпать при неактивности. Для 24/7 работы используйте платный план.

---

## 🐍 PythonAnywhere

**Хостинг специально для Python**

### Инструкция

1. **Регистрация:**
   - Перейдите на [PythonAnywhere](https://www.pythonanywhere.com/)
   - Создайте бесплатный аккаунт

2. **Открыть Bash консоль:**
   - Dashboard → "Consoles" → "Bash"

3. **Клонирование:**
   ```bash
   git clone https://github.com/ваш-username/merai-monitoring.git
   cd merai-monitoring
   ```

4. **Установка зависимостей:**
   ```bash
   pip3.12 install --user -r requirements.txt
   ```

5. **Настройка .env:**
   ```bash
   nano .env
   ```

6. **Создание always-on задачи:**
   - Dashboard → "Tasks"
   - Добавьте:
     ```
     python3.12 /home/ваш-username/merai-monitoring/merai_bot.py
     ```

**Примечание:** Бесплатный план ограничен. Для постоянной работы нужен платный аккаунт.

---

## 💻 Локальный запуск

**Для разработки и тестирования**

### Windows

```powershell
# Клонирование
git clone https://github.com/ваш-username/merai-monitoring.git
cd merai-monitoring

# Виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Установка
pip install -r requirements.txt

# Настройка
copy .env.example .env
notepad .env

# Запуск
python merai_bot.py
```

### macOS

```bash
# Клонирование
git clone https://github.com/ваш-username/merai-monitoring.git
cd merai-monitoring

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установка
pip install -r requirements.txt

# Настройка
cp .env.example .env
nano .env

# Запуск
python merai_bot.py
```

### Linux

```bash
# Клонирование
git clone https://github.com/ваш-username/merai-monitoring.git
cd merai-monitoring

# Виртуальное окружение
python3.12 -m venv venv
source venv/bin/activate

# Установка
pip install -r requirements.txt

# Настройка
cp .env.example .env
nano .env

# Запуск
python merai_bot.py
```

---

## 🔧 Советы по выбору платформы

### Для новичков:
1. **BotHost** - самый простой вариант
2. **Replit** - для быстрого тестирования

### Для продакшена:
1. **VPS** - максимальная надежность
2. **Railway** - баланс простоты и функциональности

### Для разработки:
1. **Локальный запуск** - полный контроль

---

## ⚡ Оптимизация

### Уменьшение потребления RAM

Если у вас ограничены ресурсы:

```python
# В merai_bot.py отключите ненужные функции
ENABLE_AI = False
ENABLE_ARCHIVES = False
```

### Логирование

Для продакшена настройте ротацию логов:

```bash
# Linux/VPS
sudo apt install logrotate

sudo nano /etc/logrotate.d/merai
```

Добавьте:
```
/opt/merai-monitoring/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

---

## 🐛 Диагностика проблем

### Бот не запускается

1. Проверьте логи
2. Проверьте переменные окружения
3. Проверьте версию Python (3.12+)

### Бот вылетает

1. Увеличьте RAM (если на хостинге)
2. Проверьте логи на ошибки
3. Обновите зависимости

### Не работает перехват

1. **Bot режим:** Проверьте права администратора
2. **UserBot режим:** Проверьте авторизацию

---

## 📞 Поддержка

- **Telegram:** [@mrztn](https://t.me/mrztn)
- **GitHub Issues:** [Создать issue](https://github.com/ваш-username/merai-monitoring/issues)

---

**Удачного развертывания! 🚀**

*MerAi & Monitoring v1.0 | Март 2026*
