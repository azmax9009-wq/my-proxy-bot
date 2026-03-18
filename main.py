import asyncio
import aiohttp
import hashlib
import os
import re
import time
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- УТИЛИТЫ ---
def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    try:
        with open(USERS_FILE, "r") as f: 
            return list(set([int(l.strip()) for l in f if l.strip().isdigit()]))
    except: return [USER_ID]

def save_user(user_id):
    u_id = str(user_id)
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if u_id not in users:
        with open(USERS_FILE, "a") as f: f.write(u_id + "\n")

# --- КЛАВИАТУРА ---
def get_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать в персональный VPN-центр!**\n\n"
        "Я помогу вам настроить свободный интернет через приложение **Happ**.\n"
        "Используйте кнопки меню ниже для работы.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **ИНСТРУКЦИЯ ДЛЯ ПРИЛОЖЕНИЯ HAPP**\n\n"
        "**1️⃣ Установите Happ**\n"
        "Скачайте официальное приложение для вашего телефона по ссылкам ниже.\n\n"
        "**2️⃣ Скачайте файл с настройками**\n"
        "Нажмите кнопку **'🚀 ПОЛУЧИТЬ НАСТРОЙКИ'** в меню бота и откройте файл.\n\n"
        "**3️⃣ Импорт в Happ**\n"
        "• Скопируйте весь текст из файла.\n"
        "• Откройте приложение **Happ**.\n"
        "• Нажмите иконку **'+' (Add)** в верхнем углу.\n"
        "• Выберите **'Add from Clipboard'** (Добавить из буфера).\n\n"
        "**4️⃣ Включите VPN**\n"
        "Нажмите на кнопку подключения (обычно это кнопка в центре или иконка щита). Готово! 🌍"
    )
    
    # Кнопки для скачивания Happ
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android (Google Play)", url="https://play.google.com/store/apps/details?id=com.happ.android")],
        [InlineKeyboardButton(text="🍎 iPhone (App Store)", url="https://apps.apple.com/us/app/happ-proxy/id6477543881")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                total = len(re.findall(r'vless://', content))
                caption = (
                    f"✅ **Конфигурация для Happ готова!**\n\n"
                    f"🌍 Серверов: **{total}**\n"
                    f"🕒 Обновлено: {last_update_time}\n\n"
                    f"👇 *Инструкция по настройке — кнопка '📖 Инструкция'*"
                )
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(content.encode(), filename="Happ_Configs.txt"), 
                    caption=caption, parse_mode="Markdown"
                )

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await message.answer(
        f"🖥 **МОНИТОРИНГ**\n\n"
        f"🟢 Статус: **В сети**\n"
        f"👥 Пользователей: **{len(get_all_users())}**\n"
        f"🕒 Данные от: `{last_update_time}`", 
        parse_mode="Markdown"
    )

@dp.message(F.text == "⚡ Скорость")
async def speed_test(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить тест", url="https://fast.com/ru/")]
    ])
    await message.answer("📏 Нажмите кнопку ниже, чтобы проверить скорость вашего интернета.", reply_markup=kb, parse_mode="Markdown")

# --- СИСТЕМНЫЕ ЦИКЛЫ ---
async def check_github_loop():
    global last_hash, last_update_time
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        new_hash = hashlib.md5(content.encode()).hexdigest()
                        if new_hash != last_hash:
                            now = datetime.now(pytz.timezone('Europe/Moscow'))
                            last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                            if last_hash != "start_node":
                                for uid in get_all_users():
                                    try: 
                                        await bot.send_message(
                                            uid, 
                                            f"🔔 **ОБНОВЛЕНИЕ СЕРВЕРОВ!**\n\n"
                                            f"Добавлены новые прокси для Happ.\n"
                                            f"Нажмите '🚀 ПОЛУЧИТЬ НАСТРОЙКИ', чтобы скачать новый файл."
                                        )
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="Happ Bot Active")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    all_users = get_all_users()
    now = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
    
    # Массовая рассылка при запуске
    for uid in all_users:
        try:
            await bot.send_message(
                uid, 
                f"✅ **Бот Happ VPN обновлен!**\n\n"
                f"🕒 Запуск: {now} (МСК)\n"
                f"Все системы работают штатно. Ждем обновлений на GitHub!",
                reply_markup=get_kb(), parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)
        except: pass

    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
