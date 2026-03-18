import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 # Твой ID (Админ)
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ---
def save_user(user_id):
    user_id_str = str(user_id)
    try:
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f: users = f.read().splitlines()
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
        [KeyboardButton(text="🚀 Получить прокси")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="🆘 Помощь / Связь")],
        [KeyboardButton(text="ℹ️ Статус"), KeyboardButton(text="🌐 Проверить скорость")]
    ], resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=15) as resp:
                if resp.status == 200: return (await resp.text()).strip()
                elif resp.status == 404:
                    await bot.send_message(USER_ID, "⚠️ **ВНИМАНИЕ:** Ссылка на GitHub выдает ошибку 404! Проверьте файл.")
        except: pass
    return None

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать!**\n\nЯ слежу за прокси 24/7. Используйте кнопки ниже, чтобы настроить интернет.",
        reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.answer("❌ Напишите текст: `/broadcast Привет всем!`")
    
    users = get_all_users()
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **Объявление от автора:**\n\n{text}", parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.1)
        except: pass
    await message.answer(f"✅ Сообщение отправлено {count} пользователям.")

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    help_text = (
        "👵 **ИНСТРУКЦИЯ (Hiddify):**\n\n"
        "1️⃣ Установите: [Android](https://play.google.com/store/apps/details?id=app.hiddify.com) | [iPhone](https://apps.apple.com/us/app/hiddify-next/id6473777529)\n"
        "2️⃣ Нажмите **«🚀 Получить прокси»** в боте.\n"
        "3️⃣ Откройте файл и **скопируйте** текст.\n"
        "4️⃣ В Hiddify: **«Новый профиль» (+)** -> **«Из буфера»**.\n"
        "5️⃣ Нажмите круглую кнопку в центре (она станет зеленой)."
    )
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "🆘 Помощь / Связь")
async def contact_author(message: types.Message):
    await message.answer(
        "👨‍💻 **Возникли трудности?**\n\nНапишите мне лично, я помогу настроить: @igareck",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🌐 Проверить скорость")
async def check_speed(message: types.Message):
    await message.answer(
        "🚀 **Проверьте ваш интернет:**\nПерейдите на сайт [Fast.com](https://fast.com/ru/), чтобы узнать реальную скорость после подключения.",
        parse_mode="Markdown"
    )

@dp.message(F.text == "ℹ️ Статус")
async def about_bot(message: types.Message):
    await message.answer(f"🤖 **Бот онлайн**\n🕒 Обновлено: `{last_update_time}` МСК", parse_mode="Markdown")

@dp.message(F.text == "🚀 Получить прокси")
async def manual_test(message: types.Message):
    save_user(message.from_user.id)
    proxies = await get_proxies()
    if proxies:
        file_data = proxies.encode('utf-8')
        await bot.send_document(
            message.chat.id, 
            BufferedInputFile(file_data, filename="proxies.txt"), 
            caption=f"🕒 Актуально на: {last_update_time}"
        )
    else:
        await message.answer("❌ Ошибка связи с GitHub.")

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
                    msg = "🔔 **Внимание! Обновились настройки прокси.**\nНажмите кнопку ниже, чтобы получить свежий файл."
                    for uid in get_all_users():
                        try: await bot.send_message(uid, msg, reply_markup=get_main_keyboard(), parse_mode="Markdown"); await asyncio.sleep(0.1)
                        except: pass
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

# --- ВЕБ-СЕРВЕР ---
async def handle(request): return web.Response(text="Bot Active")

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
