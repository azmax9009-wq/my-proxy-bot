import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- ФУНКЦИИ СПИСКА ---
def save_user(user_id):
    user_id_str = str(user_id)
    try:
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                with open(USERS_FILE, "r") as fr: users = fr.read().splitlines()
        if user_id_str not in users:
            with open(USERS_FILE, "a") as f: f.write(user_id_str + "\n")
            return True
    except: pass
    return False

def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    try:
        with open(USERS_FILE, "r") as f: 
            return [int(l.strip()) for l in f if l.strip().isdigit()]
    except: return [USER_ID]

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="📊 Статус системы"), KeyboardButton(text="⚡ Скорость")]
    ], resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=15) as resp:
                if resp.status == 200: return (await resp.text()).strip()
        except: pass
    return None

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать!**\n\nНажмите кнопку ниже, чтобы получить настройки или прочитать инструкцию.",
        reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )

# Исправленная команда рассылки
@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id != USER_ID:
        return 
    
    # Берем текст после команды /broadcast
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        return await message.answer("❌ Ошибка! Напишите: `/broadcast Ваш текст`", parse_mode="Markdown")
    
    broadcast_text = command_parts[1]
    users = get_all_users()
    sent_count = 0
    
    status_msg = await message.answer(f"⏳ Начинаю рассылку на {len(users)} пользователей...")
    
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **ВАЖНОЕ СООБЩЕНИЕ:**\n\n{broadcast_text}", parse_mode="Markdown")
            sent_count += 1
            await asyncio.sleep(0.05)
        except:
            continue
            
    await status_msg.edit_text(f"✅ Рассылка завершена!\nДоставлено: {sent_count} чел.")

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    help_text = (
        "📖 **ПОШАГОВОЕ РУКОВОДСТВО**\n\n"
        "1. Установите **Hiddify** на ваш телефон.\n"
        "2. Нажмите **«🚀 ПОЛУЧИТЬ НАСТРОЙКИ»**.\n"
        "3. Скопируйте текст из файла.\n"
        "4. В приложении нажмите `+` и выберите `Из буфера`.\n"
        "5. Нажмите кнопку подключения."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/hiddify-next/id6473777529")]
    ])
    await message.answer(help_text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "⚡ Скорость")
async def check_speed(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Проверить скорость", url="https://fast.com/ru/")]
    ])
    await message.answer("📏 Нажмите кнопку ниже для теста:", reply_markup=kb)

@dp.message(F.text == "📊 Статус системы")
async def about_bot(message: types.Message):
    await message.answer(f"✅ **Бот работает**\n🕒 Обновлено: `{last_update_time}` МСК", parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def get_file(message: types.Message):
    save_user(message.from_user.id)
    proxies = await get_proxies()
    if proxies:
        file_data = proxies.encode('utf-8')
        await bot.send_document(
            message.chat.id, 
            BufferedInputFile(file_data, filename="proxies.txt"), 
            caption=f"🕒 Обновлено: {last_update_time}"
        )
    else:
        await message.answer("❌ Ошибка связи. Попробуйте позже.")

# --- МОНИТОРИНГ ---
async def check_proxies_loop():
    global last_hash, last_update_time
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                if last_hash != "start_node":
                    msg = "🔔 **ОБНОВЛЕНИЕ!**\nНажмите «🚀 ПОЛУЧИТЬ НАСТРОЙКИ»."
                    for uid in get_all_users():
                        try: await bot.send_message(uid, msg); await asyncio.sleep(0.1)
                        except: pass
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def handle(request): return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
