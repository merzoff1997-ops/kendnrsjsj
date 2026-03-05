"""
MerAi & Monitoring - Advanced Telegram Bot/UserBot
Перехватчик удаленных сообщений с AI интеграцией

DISCLAIMER: Использование userbot может нарушать ToS Telegram.
Администрация не несет ответственности за последствия использования.
"""

import asyncio
import os
import json
import zipfile
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from pathlib import Path

# Импорты для Bot режима (aiogram 3.x)
try:
    from aiogram import Bot, Dispatcher, Router, F
    from aiogram.types import (
        Message, CallbackQuery, InlineKeyboardMarkup, 
        InlineKeyboardButton, LabeledPrice, PreCheckoutQuery,
        ContentType, InputFile, FSInputFile
    )
    from aiogram.filters import Command, CommandStart
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.fsm.storage.memory import MemoryStorage
    AIOGRAM_AVAILABLE = True
except ImportError:
    AIOGRAM_AVAILABLE = False
    print("⚠️ aiogram не установлен. Bot режим недоступен.")

# Импорты для UserBot режима (Pyrogram)
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message as PyrogramMessage
    from pyrogram.handlers import MessageHandler, EditedMessageHandler, DeletedMessagesHandler
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    print("⚠️ Pyrogram не установлен. UserBot режим недоступен.")

# AI библиотеки
import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== КОНФИГУРАЦИЯ ====================

class Config:
    """Конфигурация бота"""
    
    # Основные настройки
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    ADMIN_ID = 7785371505  # @mrztn
    
    # UserBot настройки (опционально)
    API_ID = os.getenv('API_ID', '')
    API_HASH = os.getenv('API_HASH', '')
    SESSION_NAME = os.getenv('SESSION_NAME', 'merai_session')
    
    # AI ключи (настраиваются через админку)
    AI_KEYS = {
        'grok': os.getenv('GROK_API_KEY', ''),
        'gemini': os.getenv('GEMINI_API_KEY', ''),
        'glm': os.getenv('GLM_API_KEY', '')
    }
    
    # Платежные настройки
    PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN', '')
    CRYPTO_ENABLED = False
    CRYPTO_WALLETS = {}
    
    # База данных (в памяти для простоты, можно заменить на SQLite)
    DATA_FILE = 'merai_data.json'

# ==================== БАЗА ДАННЫХ ====================

class Database:
    """Простая JSON база данных"""
    
    def __init__(self, filename='merai_data.json'):
        self.filename = filename
        self.data = self._load()
    
    def _load(self):
        """Загрузка данных из файла"""
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'users': {},
            'subscriptions': {},
            'linked_bots': {},
            'settings': {
                'ai_keys': Config.AI_KEYS.copy(),
                'payment_enabled': True,
                'crypto_enabled': False
            }
        }
    
    def _save(self):
        """Сохранение данных в файл"""
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def get_user(self, user_id: int) -> Dict:
        """Получить данные пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.data['users']:
            self.data['users'][user_id_str] = {
                'id': user_id,
                'username': None,
                'mode': None,  # 'bot' или 'userbot'
                'created_at': datetime.now().isoformat(),
                'plan': 'free',
                'plan_expires': None,
                'stars': 0,
                'auto_renew': False,
                'settings': {
                    'notifications': True,
                    'archive_format': 'zip'
                }
            }
            self._save()
        return self.data['users'][user_id_str]
    
    def update_user(self, user_id: int, updates: Dict):
        """Обновить данные пользователя"""
        user = self.get_user(user_id)
        user.update(updates)
        self._save()
    
    def get_subscription(self, user_id: int) -> Dict:
        """Получить подписку пользователя"""
        user = self.get_user(user_id)
        return {
            'plan': user['plan'],
            'expires': user['plan_expires'],
            'auto_renew': user['auto_renew']
        }
    
    def set_subscription(self, user_id: int, plan: str, days: int):
        """Установить подписку"""
        user = self.get_user(user_id)
        
        if user['plan_expires']:
            expires = datetime.fromisoformat(user['plan_expires'])
            if expires > datetime.now():
                new_expires = expires + timedelta(days=days)
            else:
                new_expires = datetime.now() + timedelta(days=days)
        else:
            new_expires = datetime.now() + timedelta(days=days)
        
        self.update_user(user_id, {
            'plan': plan,
            'plan_expires': new_expires.isoformat()
        })
    
    def add_linked_bot(self, user_id: int, bot_token: str):
        """Добавить связанный бот"""
        user_id_str = str(user_id)
        if user_id_str not in self.data['linked_bots']:
            self.data['linked_bots'][user_id_str] = []
        self.data['linked_bots'][user_id_str].append({
            'token': bot_token,
            'added_at': datetime.now().isoformat()
        })
        self._save()
    
    def get_ai_key(self, provider: str) -> str:
        """Получить AI ключ"""
        return self.data['settings']['ai_keys'].get(provider, '')
    
    def set_ai_key(self, provider: str, key: str):
        """Установить AI ключ"""
        self.data['settings']['ai_keys'][provider] = key
        self._save()

# Глобальная база данных
db = Database()

# ==================== ПЛАНЫ ПОДПИСКИ ====================

SUBSCRIPTION_PLANS = {
    'starter': {
        'name': '🌟 Starter',
        'price_stars': 100,
        'price_rub': 149,
        'days': 7,
        'features': [
            '✅ Базовое сохранение удаленных сообщений',
            '✅ До 100 сообщений/день',
            '✅ Поддержка текста и фото'
        ]
    },
    'pro': {
        'name': '⭐ Pro',
        'price_stars': 250,
        'price_rub': 349,
        'days': 30,
        'features': [
            '✅ Все функции Starter',
            '✅ Неограниченные сообщения',
            '✅ Видео, аудио, документы',
            '✅ Архивация целых диалогов',
            '✅ AI ассистент (GPT-4)'
        ]
    },
    'premium': {
        'name': '💎 Premium',
        'price_stars': 500,
        'price_rub': 699,
        'days': 90,
        'features': [
            '✅ Все функции Pro',
            '✅ Приоритетная поддержка',
            '✅ Расширенная аналитика',
            '✅ Подключение собственного бота (+7 дней)',
            '✅ Множественные AI модели'
        ]
    }
}

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def create_plan_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора плана"""
    buttons = []
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{plan['name']} - {plan['price_stars']} ⭐",
                callback_data=f"buy_{plan_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def create_admin_keyboard() -> InlineKeyboardMarkup:
    """Создать админ-панель"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="🤖 AI Ключи", callback_data="admin_ai")],
        [InlineKeyboardButton(text="💰 Платежи", callback_data="admin_payments")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

def create_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Создать главное меню"""
    buttons = [
        [InlineKeyboardButton(text="📦 Мои подписки", callback_data="my_subscriptions")],
        [InlineKeyboardButton(text="💎 Купить план", callback_data="buy_plan")],
        [InlineKeyboardButton(text="🤖 AI Помощник", callback_data="ai_chat")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="📖 Помощь", callback_data="help")]
    ]
    
    # Админ-панель для админа
    if user_id == Config.ADMIN_ID:
        buttons.append([InlineKeyboardButton(text="🔐 Админ-панель", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def format_deleted_message(msg_data: Dict) -> str:
    """Форматировать уведомление об удаленном сообщении"""
    chat_name = msg_data.get('chat_name', 'Неизвестный чат')
    user_name = msg_data.get('user_name', 'Неизвестный пользователь')
    msg_type = msg_data.get('type', 'text')
    content = msg_data.get('content', '')
    timestamp = msg_data.get('timestamp', datetime.now().isoformat())
    
    text = f"""
🗑 <b>Удалено сообщение</b>

📱 <b>Чат:</b> {chat_name}
👤 <b>Пользователь:</b> {user_name}
🕒 <b>Время:</b> {timestamp}
📝 <b>Тип:</b> {msg_type}

"""
    
    if msg_type == 'text' and content:
        text += f"💬 <b>Текст:</b>\n<blockquote>{content}</blockquote>"
    elif msg_type in ['photo', 'video', 'voice', 'video_note']:
        text += f"📎 <b>Медиа:</b> {msg_type}\n<i>(Файл сохранен)</i>"
    
    return text

async def create_archive(messages: List[Dict], user_id: int) -> io.BytesIO:
    """Создать ZIP архив удаленных сообщений"""
    archive = io.BytesIO()
    
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zf:
        # HTML отчет
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Удаленные сообщения - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .message {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #0088cc; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 10px; }}
        .content {{ margin-top: 10px; }}
        .deleted {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🗑 Архив удаленных сообщений</h1>
        <p>Создано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>
"""
        
        for i, msg in enumerate(messages, 1):
            html_content += f"""
    <div class="message deleted">
        <div class="meta">
            <strong>#{i}</strong> | 
            <strong>Чат:</strong> {msg.get('chat_name', 'N/A')} | 
            <strong>От:</strong> {msg.get('user_name', 'N/A')} | 
            <strong>Время:</strong> {msg.get('timestamp', 'N/A')}
        </div>
        <div class="content">
            <strong>Тип:</strong> {msg.get('type', 'text')}<br>
"""
            
            if msg.get('content'):
                html_content += f"            <strong>Текст:</strong> {msg['content']}<br>\n"
            
            if msg.get('file_path'):
                html_content += f"            <strong>Файл:</strong> <a href='{msg['file_path']}'>{msg['file_path']}</a><br>\n"
            
            html_content += "        </div>\n    </div>\n"
        
        html_content += """
</body>
</html>
"""
        
        zf.writestr('deleted_messages.html', html_content.encode('utf-8'))
        
        # JSON с данными
        zf.writestr('messages.json', json.dumps(messages, indent=2, ensure_ascii=False).encode('utf-8'))
        
        # README
        readme = """
MerAi & Monitoring - Архив удаленных сообщений

Содержимое:
- deleted_messages.html - визуальный отчет (откройте в браузере)
- messages.json - данные в формате JSON
- media/ - папка с медиафайлами (если есть)

Дата создания: {}

ВНИМАНИЕ: Этот архив содержит конфиденциальную информацию.
Храните его в безопасном месте.
""".format(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        
        zf.writestr('README.txt', readme.encode('utf-8'))
    
    archive.seek(0)
    return archive

# ==================== AI ИНТЕГРАЦИЯ ====================

class AIAssistant:
    """AI помощник с поддержкой разных провайдеров"""
    
    @staticmethod
    async def chat(provider: str, prompt: str, user_message: str) -> str:
        """Отправить запрос к AI"""
        api_key = db.get_ai_key(provider)
        
        if not api_key:
            return "❌ API ключ не настроен. Обратитесь к администратору."
        
        try:
            if provider == 'gemini':
                return await AIAssistant._gemini_request(api_key, prompt, user_message)
            elif provider == 'grok':
                return await AIAssistant._grok_request(api_key, prompt, user_message)
            elif provider == 'glm':
                return await AIAssistant._glm_request(api_key, prompt, user_message)
            else:
                return "❌ Неизвестный AI провайдер"
        except Exception as e:
            logger.error(f"AI error: {e}")
            return f"❌ Ошибка AI: {str(e)}"
    
    @staticmethod
    async def _gemini_request(api_key: str, prompt: str, message: str) -> str:
        """Gemini API запрос"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{prompt}\n\nПользователь: {message}"
                }]
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    return f"❌ Ошибка API: {resp.status}"
    
    @staticmethod
    async def _grok_request(api_key: str, prompt: str, message: str) -> str:
        """Grok API запрос (пример, актуальный endpoint может отличаться)"""
        # Примечание: Это пример, реальный API Grok может иметь другую структуру
        return "⚠️ Grok API в разработке. Используйте Gemini."
    
    @staticmethod
    async def _glm_request(api_key: str, prompt: str, message: str) -> str:
        """GLM API запрос"""
        # Примечание: Это пример для ChatGLM
        return "⚠️ GLM API в разработке. Используйте Gemini."

# ==================== BOT РЕЖИМ ====================

class BotMode:
    """Telegram Bot режим (официальный API)"""
    
    def __init__(self, token: str):
        if not AIOGRAM_AVAILABLE:
            raise ImportError("aiogram не установлен")
        
        self.bot = Bot(token=token)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.router = Router()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков"""
        
        # Команды
        self.router.message(CommandStart())(self.cmd_start)
        self.router.message(Command("admin"))(self.cmd_admin)
        self.router.message(Command("help"))(self.cmd_help)
        self.router.message(Command("plans"))(self.cmd_plans)
        
        # Callback кнопки
        self.router.callback_query(F.data == "main_menu")(self.callback_main_menu)
        self.router.callback_query(F.data == "buy_plan")(self.callback_buy_plan)
        self.router.callback_query(F.data.startswith("buy_"))(self.callback_buy_subscription)
        self.router.callback_query(F.data == "my_subscriptions")(self.callback_my_subscriptions)
        self.router.callback_query(F.data == "admin_panel")(self.callback_admin_panel)
        self.router.callback_query(F.data == "admin_ai")(self.callback_admin_ai)
        self.router.callback_query(F.data == "help")(self.callback_help)
        
        # Pre-checkout для Stars
        self.router.pre_checkout_query()(self.process_pre_checkout)
        
        # Успешный платеж
        self.router.message(F.successful_payment)(self.process_successful_payment)
        
        # Регистрация роутера
        self.dp.include_router(self.router)
    
    async def cmd_start(self, message: Message):
        """Команда /start"""
        user = db.get_user(message.from_user.id)
        
        welcome_text = f"""
👋 <b>Добро пожаловать в MerAi & Monitoring!</b>

<i>Ваш персональный помощник для сохранения удаленных сообщений и AI-ассистент</i>

🔹 <b>Ваш режим:</b> {user.get('mode', 'Не выбран')}
🔹 <b>Подписка:</b> {user.get('plan', 'Free')}

Выберите действие:
"""
        
        await message.answer(
            welcome_text,
            reply_markup=create_main_keyboard(message.from_user.id),
            parse_mode='HTML'
        )
    
    async def cmd_admin(self, message: Message):
        """Команда /admin"""
        if message.from_user.id != Config.ADMIN_ID:
            await message.answer("❌ У вас нет прав администратора")
            return
        
        await message.answer(
            "🔐 <b>Админ-панель</b>\n\nВыберите раздел:",
            reply_markup=create_admin_keyboard(),
            parse_mode='HTML'
        )
    
    async def cmd_help(self, message: Message):
        """Команда /help"""
        help_text = """
📖 <b>Инструкция по использованию</b>

<b>🤖 BOT РЕЖИМ (Telegram Premium):</b>
1. Добавьте бота в группу/канал как администратора
2. Бот будет отслеживать удаления в этой группе
3. Ограничения: не видит личные сообщения других пользователей

<b>👤 USERBOT РЕЖИМ:</b>
1. Получите API_ID и API_HASH на my.telegram.org
2. Введите их в настройках
3. Авторизуйтесь через свой аккаунт
4. ⚠️ ВНИМАНИЕ: нарушает ToS Telegram, риск блокировки!

<b>Возможности:</b>
✅ Сохранение удаленных текстовых сообщений
✅ Сохранение фото, видео, документов
✅ Архивация целых диалогов (ZIP)
✅ AI помощник для анализа сообщений
✅ Красивые уведомления

<b>Команды:</b>
/start - Главное меню
/plans - Тарифные планы
/help - Эта справка
/admin - Админ-панель (только для админа)

⚠️ <b>DISCLAIMER:</b>
Администрация не несет ответственности за использование userbot режима и последствия нарушения ToS Telegram. Используйте на свой риск.
"""
        
        await message.answer(help_text, parse_mode='HTML')
    
    async def cmd_plans(self, message: Message):
        """Команда /plans"""
        await message.answer(
            "💎 <b>Доступные тарифы</b>\n\nВыберите подходящий план:",
            reply_markup=create_plan_keyboard(),
            parse_mode='HTML'
        )
    
    async def callback_main_menu(self, callback: CallbackQuery):
        """Главное меню"""
        user = db.get_user(callback.from_user.id)
        
        text = f"""
👋 <b>Главное меню</b>

🔹 <b>Подписка:</b> {user.get('plan', 'Free')}
🔹 <b>Режим:</b> {user.get('mode', 'Не выбран')}
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=create_main_keyboard(callback.from_user.id),
            parse_mode='HTML'
        )
        await callback.answer()
    
    async def callback_buy_plan(self, callback: CallbackQuery):
        """Выбор плана"""
        plans_text = "💎 <b>Тарифные планы</b>\n\n"
        
        for plan_id, plan in SUBSCRIPTION_PLANS.items():
            plans_text += f"<b>{plan['name']}</b>\n"
            plans_text += f"💰 {plan['price_stars']} ⭐ или {plan['price_rub']} ₽\n"
            plans_text += f"⏰ {plan['days']} дней\n\n"
            for feature in plan['features']:
                plans_text += f"{feature}\n"
            plans_text += "\n"
        
        await callback.message.edit_text(
            plans_text,
            reply_markup=create_plan_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
    
    async def callback_buy_subscription(self, callback: CallbackQuery):
        """Покупка подписки"""
        plan_id = callback.data.replace("buy_", "")
        plan = SUBSCRIPTION_PLANS.get(plan_id)
        
        if not plan:
            await callback.answer("❌ План не найден", show_alert=True)
            return
        
        # Создание инвойса для Stars
        prices = [LabeledPrice(label=plan['name'], amount=plan['price_stars'])]
        
        try:
            await self.bot.send_invoice(
                chat_id=callback.from_user.id,
                title=plan['name'],
                description=f"Подписка на {plan['days']} дней",
                payload=f"plan_{plan_id}",
                currency="XTR",  # Telegram Stars
                prices=prices
            )
            await callback.answer("✅ Инвойс отправлен")
        except Exception as e:
            logger.error(f"Invoice error: {e}")
            await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    
    async def callback_my_subscriptions(self, callback: CallbackQuery):
        """Мои подписки"""
        user = db.get_user(callback.from_user.id)
        sub = db.get_subscription(callback.from_user.id)
        
        text = f"""
📦 <b>Мои подписки</b>

<b>Текущий план:</b> {sub['plan']}
<b>Истекает:</b> {sub['expires'] if sub['expires'] else 'Не активна'}
<b>Автопродление:</b> {'✅ Включено' if sub['auto_renew'] else '❌ Отключено'}

<b>Звезды:</b> {user.get('stars', 0)} ⭐
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить план", callback_data="buy_plan")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        await callback.answer()
    
    async def callback_admin_panel(self, callback: CallbackQuery):
        """Админ-панель"""
        if callback.from_user.id != Config.ADMIN_ID:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        stats = {
            'total_users': len(db.data['users']),
            'active_subs': sum(1 for u in db.data['users'].values() 
                             if u.get('plan') != 'free' and u.get('plan_expires'))
        }
        
        text = f"""
🔐 <b>Админ-панель</b>

📊 <b>Статистика:</b>
👥 Всего пользователей: {stats['total_users']}
💎 Активных подписок: {stats['active_subs']}

Выберите действие:
"""
        
        await callback.message.edit_text(
            text,
            reply_markup=create_admin_keyboard(),
            parse_mode='HTML'
        )
        await callback.answer()
    
    async def callback_admin_ai(self, callback: CallbackQuery):
        """Настройка AI ключей"""
        if callback.from_user.id != Config.ADMIN_ID:
            await callback.answer("❌ Доступ запрещен", show_alert=True)
            return
        
        keys = db.data['settings']['ai_keys']
        text = f"""
🤖 <b>AI Ключи</b>

<b>Gemini:</b> {'✅ Настроен' if keys.get('gemini') else '❌ Не настроен'}
<b>Grok:</b> {'✅ Настроен' if keys.get('grok') else '❌ Не настроен'}
<b>GLM:</b> {'✅ Настроен' if keys.get('glm') else '❌ Не настроен'}

<i>Для изменения ключей отредактируйте конфигурационный файл</i>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_panel")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='HTML')
        await callback.answer()
    
    async def callback_help(self, callback: CallbackQuery):
        """Справка"""
        await self.cmd_help(callback.message)
        await callback.answer()
    
    async def process_pre_checkout(self, pre_checkout: PreCheckoutQuery):
        """Обработка pre-checkout"""
        await pre_checkout.answer(ok=True)
    
    async def process_successful_payment(self, message: Message):
        """Обработка успешного платежа"""
        payload = message.successful_payment.invoice_payload
        
        if payload.startswith("plan_"):
            plan_id = payload.replace("plan_", "")
            plan = SUBSCRIPTION_PLANS.get(plan_id)
            
            if plan:
                db.set_subscription(message.from_user.id, plan_id, plan['days'])
                
                await message.answer(
                    f"""
✅ <b>Оплата успешна!</b>

Вы приобрели план <b>{plan['name']}</b>
Подписка активна на {plan['days']} дней

Спасибо за покупку! 🎉
""",
                    parse_mode='HTML'
                )
    
    async def start(self):
        """Запуск бота"""
        logger.info("🤖 Запуск Bot режима...")
        await self.dp.start_polling(self.bot)

# ==================== USERBOT РЕЖИМ ====================

class UserBotMode:
    """Telegram UserBot режим (Pyrogram)"""
    
    def __init__(self, api_id: str, api_hash: str, session_name: str):
        if not PYROGRAM_AVAILABLE:
            raise ImportError("Pyrogram не установлен")
        
        self.app = Client(
            session_name,
            api_id=api_id,
            api_hash=api_hash
        )
        
        self._setup_handlers()
        self.deleted_cache = []  # Кэш для массовых удалений
    
    def _setup_handlers(self):
        """Настройка обработчиков UserBot"""
        
        @self.app.on_message(filters.all)
        async def save_message(client, message: PyrogramMessage):
            """Сохранение всех сообщений для отслеживания удалений"""
            # Здесь можно реализовать кэширование сообщений
            pass
        
        @self.app.on_edited_message(filters.all)
        async def handle_edit(client, message: PyrogramMessage):
            """Обработка редактирования"""
            # Отправка уведомления о редактировании
            pass
        
        # Примечание: Pyrogram не имеет прямого обработчика удалений
        # Нужно использовать raw updates или альтернативные методы
    
    async def start(self):
        """Запуск UserBot"""
        logger.info("👤 Запуск UserBot режима...")
        logger.warning("⚠️ UserBot режим нарушает ToS Telegram!")
        await self.app.run()

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

async def main():
    """Главная функция запуска"""
    
    print("""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║       MerAi & Monitoring v1.0                     ║
║       Telegram Message Recovery & AI Bot          ║
║                                                   ║
║       DISCLAIMER: Используйте на свой риск        ║
║       Администрация не несет ответственности      ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
""")
    
    print("\n🔧 Выберите режим работы:\n")
    print("1. 🤖 Bot режим (Telegram Premium API)")
    print("2. 👤 UserBot режим (⚠️ нарушает ToS)")
    print("3. 🔄 Гибридный режим (оба одновременно)")
    
    mode = input("\nВведите номер (1-3): ").strip()
    
    if mode == "1":
        if not Config.BOT_TOKEN:
            print("❌ Ошибка: BOT_TOKEN не установлен в переменных окружения")
            return
        
        bot = BotMode(Config.BOT_TOKEN)
        await bot.start()
    
    elif mode == "2":
        if not Config.API_ID or not Config.API_HASH:
            print("❌ Ошибка: API_ID и API_HASH не установлены")
            return
        
        userbot = UserBotMode(Config.API_ID, Config.API_HASH, Config.SESSION_NAME)
        await userbot.start()
    
    elif mode == "3":
        if not Config.BOT_TOKEN or not Config.API_ID or not Config.API_HASH:
            print("❌ Ошибка: Не все параметры установлены")
            return
        
        # Запуск обоих режимов параллельно
        bot = BotMode(Config.BOT_TOKEN)
        userbot = UserBotMode(Config.API_ID, Config.API_HASH, Config.SESSION_NAME)
        
        await asyncio.gather(
            bot.start(),
            userbot.start()
        )
    
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
