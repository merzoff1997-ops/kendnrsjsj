#!/bin/bash
# MerAi & Monitoring - Автоматическая установка
# Для Linux/macOS

set -e

echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║       MerAi & Monitoring - Установка              ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Проверка Python
echo "🔍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.12 или выше."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION найден"

# Проверка pip
echo "🔍 Проверка pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip не найден. Установите pip."
    exit 1
fi
echo "✅ pip найден"

# Создание виртуального окружения
echo ""
echo "📦 Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "⚠️  venv уже существует. Удалить? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi
echo "✅ Виртуальное окружение создано"

# Активация виртуального окружения
echo ""
echo "🔌 Активация окружения..."
source venv/bin/activate
echo "✅ Окружение активировано"

# Обновление pip
echo ""
echo "📈 Обновление pip..."
pip install --upgrade pip --quiet
echo "✅ pip обновлен"

# Установка зависимостей
echo ""
echo "📥 Установка зависимостей..."
pip install -r requirements.txt --quiet
echo "✅ Зависимости установлены"

# Создание .env файла
echo ""
if [ -f ".env" ]; then
    echo "⚠️  .env файл уже существует. Пропускаем..."
else
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "✅ .env файл создан"
    echo ""
    echo "⚠️  ВАЖНО: Отредактируйте .env файл и добавьте свои данные:"
    echo "   - BOT_TOKEN (обязательно)"
    echo "   - API_ID и API_HASH (опционально, для UserBot)"
    echo "   - AI ключи (опционально)"
fi

# Проверка конфигурации
echo ""
echo "🔐 Проверка конфигурации..."
if grep -q "your_bot_token_here" .env; then
    echo "⚠️  BOT_TOKEN не настроен!"
    echo "   Получите токен у @BotFather и добавьте в .env файл"
    TOKEN_SET=false
else
    echo "✅ BOT_TOKEN настроен"
    TOKEN_SET=true
fi

# Финальные инструкции
echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║                                                   ║"
echo "║       ✅ Установка завершена!                     ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Отредактируйте .env файл:"
echo "   nano .env"
echo ""
echo "2. Добавьте ваш BOT_TOKEN от @BotFather"
echo ""
echo "3. (Опционально) Добавьте API_ID и API_HASH для UserBot режима"
echo ""
echo "4. Запустите бота:"
echo "   source venv/bin/activate  # Если еще не активировано"
echo "   python merai_bot.py"
echo ""
echo "📖 Полная документация: README.md"
echo "⚠️  Условия использования: TERMS_AND_PRIVACY.md"
echo ""
echo "Поддержка: @mrztn"
echo ""
