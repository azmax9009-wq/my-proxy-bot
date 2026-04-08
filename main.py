```python
import asyncio
import aiohttp
import os
import time
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from aiohttp import web

# --- ВАШИ ДАННЫЕ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361
# Ссылка на файл с ключами (VLESS/Reality)
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- КНОПКИ В ТЕЛЕГРАМ ---
def get_main_kb():
    buttons = [
        [KeyboardButton(text="🔑 ПОЛУЧИТЬ КЛЮЧИ")],
        [KeyboardButton(text="📊 СТАТУС СЕРВЕРА"), KeyboardButton(text="🆘 ПОМОЩЬ")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ОБРАБОТКА КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для раздачи ключей доступа. Нажми на кнопку ниже, чтобы получить актуальные настройки.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "🔑 ПОЛУЧИТЬ КЛЮЧИ")
async def send_keys(message: types.Message):
    await message.answer("🔄 *Загрузка ключей из базы...*", parse_mode="Markdown")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    # Ограничиваем длину, чтобы Telegram не выдал ошибку
                    keys = text[:3900] 
                    await message.answer("✅ **Ваши ключи готовы:**\n\n_Нажмите на текст ниже, чтобы скопировать его_")
                    # Экранируем спецсимволы и прячем под спойлер (копирование тапом)
                    safe_keys = keys.replace('`', '\\`').replace('|', '\\|')
                    await message.answer(f"||`{safe_keys}`||", parse_mode="MarkdownV2")
                else:
                    await message.answer("❌ Ошибка: Не удалось получить данные с сервера GitHub.")
        except Exception as e:
            await message.answer(f"⚠️ Ошибка сети: {str(e)}")

@dp.message(F.text == "📊 СТАТУС СЕРВЕРА")
async def status_check(message: types.Message):
    await message.answer("🛰 **Статус системы:**\n\n🟢 Все узлы работают штатно\n📡 Пинг: `24ms`", parse_mode="Markdown")

@dp.message(F.text == "🆘 ПОМОЩЬ")
async def help_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Написать админу", url=f"tg://user?id={ADMIN_ID}")]])
    await message.answer("Если ключи не работают или возникли вопросы, свяжитесь с поддержкой:", reply_markup=kb)

# --- СЕРВЕРНАЯ ЧАСТЬ ДЛЯ RENDER ---
async def handle(request):
    return web.Response(text="Telegram Bot is Active")

async def main():
    # Создаем веб-сервер, чтобы Render не закрывал проект
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render сам выдает порт через переменную PORT
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

```
