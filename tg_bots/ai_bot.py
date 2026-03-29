import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import openai
import httpx
import aiohttp

# ==================== КОНФИГУРАЦИЯ ====================
TELEGRAM_TOKEN = ''
OPENROUTER_API_KEY = ''

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Данные пользователей
user_data: Dict[int, Dict[str, Any]] = {}

# Модели для разных режимов (бесплатные)
MODELS = {
    'normal': '',
    'code': '',
    'creative': ''
}


# ==================== ФУНКЦИИ ====================
def get_user(user_id: int):
    if user_id not in user_data:
        user_data[user_id] = {
            'count': 0,
            'history': [],
            'last_request': 0,
            'mode': 'normal',
            'temperature': 0.7,
            'waiting_for_response': False  # Флаг ожидания ответа
        }
    return user_data[user_id]


def get_mode_emoji(mode: str) -> str:
    modes = {
        'normal': '⚖️',
        'code': '💻',
        'creative': '🎨'
    }
    return modes.get(mode, '⚖️')


# ==================== АСИНХРОННЫЙ ЗАПРОС К OPENROUTER ====================
async def ask_nemotron(prompt: str, user_id: int) -> str:
    user = get_user(user_id)

    # Защита от двойных запросов
    if user.get('waiting_for_response', False):
        return "⏳ Подождите, я еще отвечаю на предыдущий вопрос..."

    user['waiting_for_response'] = True

    try:
        # Защита от частых запросов
        now = time.time()
        if now - user['last_request'] < 3:  # Увеличил до 3 секунд
            await asyncio.sleep(1)

        logger.info(f"🔄 Запрос от user_{user_id} в режиме {user['mode']}")

        # Системные промпты
        system_prompts = {
            'normal': "Ты - полезный ассистент. Отвечай на русском языке кратко и по делу.",
            'code': "Ты - эксперт по программированию. Отвечай на русском, давай готовый код с объяснениями. Будь конкретным.",
            'creative': "Ты - креативный помощник. Отвечай на русском творчески, с идеями и вдохновением."
        }

        # Используем aiohttp для асинхронного запроса
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://t.me/nemotron_bot",
                "X-Title": "Nvidia Nemotron Bot",
            }

            data = {
                "model": MODELS[user['mode']],
                "messages": [
                    {"role": "system", "content": system_prompts[user['mode']]},
                    {"role": "user", "content": prompt[:1500]}  # Уменьшил до 1500 для скорости
                ],
                "temperature": user['temperature'],
                "max_tokens": 800,  # Уменьшил для скорости
                "top_p": 0.9
            }

            # Добавляем таймаут
            timeout = aiohttp.ClientTimeout(total=30)  # 30 секунд максимум

            async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=timeout
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    answer = result['choices'][0]['message']['content']

                    # Обновляем статистику
                    user['count'] += 1
                    user['last_request'] = time.time()
                    user['history'].append(f"Q: {prompt[:30]}...")

                    logger.info(f"✅ Ответ получен, длина: {len(answer)} символов")
                    return answer

                elif response.status == 429:
                    logger.warning("⚠️ Too many requests")
                    return "⚠️ Слишком много запросов к API. Подождите минуту."
                else:
                    error_text = await response.text()
                    logger.error(f"❌ API Error {response.status}: {error_text}")

                    if response.status == 402:
                        return "❌ Бесплатный лимит модели исчерпан. Попробуйте позже."
                    else:
                        return f"❌ Ошибка API: {response.status}"

    except asyncio.TimeoutError:
        logger.error("⏰ Таймаут запроса к API")
        return "⏰ Превышено время ожидания. Попробуйте еще раз."

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        return f"❌ Произошла ошибка. Попробуйте позже."

    finally:
        user['waiting_for_response'] = False


# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="stats"),
         InlineKeyboardButton("⚙️ Режимы", callback_data="modes")],
        [InlineKeyboardButton("🌡️ Температура", callback_data="temp"),
         InlineKeyboardButton("🧹 Очистить", callback_data="clear")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_modes_keyboard(user_id: int):
    user = get_user(user_id)
    current = user['mode']

    keyboard = [
        [InlineKeyboardButton(f"{'✅ ' if current == 'normal' else ''}⚖️ Обычный", callback_data="mode_normal")],
        [InlineKeyboardButton(f"{'✅ ' if current == 'code' else ''}💻 Программист", callback_data="mode_code")],
        [InlineKeyboardButton(f"{'✅ ' if current == 'creative' else ''}🎨 Креативный", callback_data="mode_creative")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_temp_keyboard(user_id: int):
    user = get_user(user_id)
    temp = user['temperature']

    keyboard = [
        [InlineKeyboardButton(f"{'✅ ' if temp == 0.3 else ''}❄️ Холодно (0.3)", callback_data="temp_0.3")],
        [InlineKeyboardButton(f"{'✅ ' if temp == 0.7 else ''}⚖️ Нормально (0.7)", callback_data="temp_0.7")],
        [InlineKeyboardButton(f"{'✅ ' if temp == 1.0 else ''}🔥 Горячо (1.0)", callback_data="temp_1.0")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id)

    welcome = (
        f"🚀 **Привет, {user.first_name}!**\n\n"
        "Я **AI-ассистент** на базе OpenRouter!\n\n"
        "✨ **Возможности:**\n"
        "• 3 режима работы\n"
        "• Настройка креативности\n"
        "• **ПОЛНОСТЬЮ БЕСПЛАТНО**\n\n"
        "⚠️ **Важно:** Бесплатные модели могут отвечать медленно\n\n"
        "⬇️ **Просто напиши сообщение!**"
    )

    await update.message.reply_text(
        welcome,
        reply_markup=get_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    message_text = update.message.text

    # Проверка длины
    if len(message_text) > 2000:
        await update.message.reply_text("❌ Слишком длинное сообщение (макс. 2000 символов)")
        return

    # Проверка на пустое сообщение
    if not message_text.strip():
        await update.message.reply_text("❌ Пустое сообщение")
        return

    # Показываем "печатает..."
    await context.bot.send_chat_action(chat_id=user_id, action="typing")

    # Отправляем промежуточное сообщение
    wait_msg = await update.message.reply_text(
        f"{get_mode_emoji(user['mode'])} Думаю... ⏳"
    )

    # Получаем ответ
    response = await ask_nemotron(message_text, user_id)

    # Удаляем промежуточное сообщение
    await wait_msg.delete()

    # Отправляем ответ
    mode_emoji = get_mode_emoji(user['mode'])

    # Разбиваем длинные сообщения
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            part = response[i:i + 4000]
            await update.message.reply_text(f"{mode_emoji} {part}")
    else:
        await update.message.reply_text(f"{mode_emoji} {response}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user = get_user(user_id)

    if query.data == "stats":
        stats = (
            f"📊 **Статистика**\n\n"
            f"👤 Пользователь: {update.effective_user.first_name}\n"
            f"📝 Сообщений: {user['count']}\n"
            f"⚙️ Режим: {user['mode']}\n"
            f"🌡️ Температура: {user['temperature']}\n"
            f"⏳ Ожидание ответа: {'✅' if user.get('waiting_for_response') else '❌'}\n"
            f"💰 **БЕСПЛАТНО**"
        )
        await query.edit_message_text(stats, parse_mode=ParseMode.MARKDOWN)
        await query.edit_message_reply_markup(reply_markup=get_main_keyboard())

    elif query.data == "modes":
        await query.edit_message_text(
            "⚙️ **Выбери режим:**",
            reply_markup=get_modes_keyboard(user_id),
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == "temp":
        await query.edit_message_text(
            "🌡️ **Настройка температуры:**\n\n"
            "❄️ Холодно (0.3) - точные ответы\n"
            "⚖️ Нормально (0.7) - сбалансировано\n"
            "🔥 Горячо (1.0) - креативные ответы",
            reply_markup=get_temp_keyboard(user_id),
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data == "clear":
        user['count'] = 0
        user['history'] = []
        user['waiting_for_response'] = False
        await query.edit_message_text("🧹 **История очищена!**", parse_mode=ParseMode.MARKDOWN)
        await query.edit_message_reply_markup(reply_markup=get_main_keyboard())

    elif query.data == "about":
        about = (
            "ℹ️ **О боте**\n\n"
            "🤖 **AI-ассистент на OpenRouter**\n"
            "💰 **ПОЛНОСТЬЮ БЕСПЛАТНО**\n\n"
            "⚙️ **Режимы:**\n"
            "• Обычный - для всего\n"
            "• Программист - для кода\n"
            "• Креативный - для творчества\n\n"
            "🌡️ **Температура:**\n"
            "• 0.3 - точные ответы\n"
            "• 0.7 - сбалансировано\n"
            "• 1.0 - креативно\n\n"
            "⚠️ Бесплатные модели могут отвечать медленно\n\n"
            "🚀 Просто и мощно!"
        )
        await query.edit_message_text(about, parse_mode=ParseMode.MARKDOWN)
        await query.edit_message_reply_markup(reply_markup=get_main_keyboard())

    elif query.data == "back":
        await query.edit_message_text(
            "🚀 **Главное меню**",
            reply_markup=get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

    elif query.data.startswith("mode_"):
        mode = query.data.replace("mode_", "")
        user['mode'] = mode
        descriptions = {
            'normal': '⚖️ Обычный режим',
            'code': '💻 Режим программиста',
            'creative': '🎨 Креативный режим'
        }
        await query.edit_message_text(
            f"✅ Режим изменен!\n\n{descriptions.get(mode, '')}",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.edit_message_reply_markup(reply_markup=get_main_keyboard())

    elif query.data.startswith("temp_"):
        temp = float(query.data.replace("temp_", ""))
        user['temperature'] = temp
        descriptions = {
            0.3: '❄️ Точные ответы',
            0.7: '⚖️ Сбалансированные',
            1.0: '🔥 Креативные'
        }
        await query.edit_message_text(
            f"✅ Температура изменена на {temp}!\n\n{descriptions.get(temp, '')}",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.edit_message_reply_markup(reply_markup=get_main_keyboard())


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Произошла техническая ошибка. Попробуйте позже."
            )
    except:
        pass


# ==================== ЗАПУСК ====================
def main():
    print("\n" + "=" * 50)
    print("🚀 AI-БОТ ЗАПУСКАЕТСЯ!")
    print("=" * 50)
    print("✅ Модель: Бесплатные модели OpenRouter")
    print("💰 Статус: БЕСПЛАТНО")
    print("⚠️ Бесплатные модели могут работать медленно")
    print("=" * 50 + "\n")

    try:
        # Создаем приложение
        app = Application.builder().token(TELEGRAM_TOKEN).build()

        # Добавляем обработчики
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button_callback))

        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)

        # Запускаем
        print("✅ Бот готов к работе!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {e}")
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте интернет-соединение и токен бота")


if __name__ == '__main__':
    main()
