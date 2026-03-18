import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание сканирования..."

# --- БАЗА ПОЛЬЗОВАТЕЛЕЙ ---
def save_user(user_id):
    user_id_str = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write(user_id_str + "\n")
        return True
    with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if user_id_str not in users:
        with open(USERS_FILE, "a") as f: f.write(user_id_str + "\n")
        return True
    return False

def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    with open(USERS_FILE, "r") as f: return [int(l.strip()) for l in f if l.strip().isdigit()]

async def notify_admin(user: types.User, action: str):
    if user.id != USER_ID:
        info = f"👤 **Активность:**\n• Имя: {user.full_name}\n• ID: `{user.id}`\n• Действие: {action}"
        try: await bot.send_message(USER_ID, info, parse_mode="Markdown")
        except: pass

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🚀 Получить прокси")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as resp:
                if resp.status == 200: return (await resp.text()).strip()
        except: pass
    return None

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await notify_admin(message.from_user, "Запустил бота")
    await message.answer("👋 **Добро пожаловать!**\nИспользуйте кнопки внизу.", parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    await notify_admin(message.from_user, "Смотрит инструкцию")
    help_text = (
        "👵👴 **ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:**\n\n"
        "1️⃣ **Установите Hiddify:**\n"
        "📱 [Android](https://play.google.com/store/apps/details?id=app.hiddify.com)\n"
        "🍎 [iPhone](https://apps.apple.com/us/app/hiddify-next/id6473777529)\n\n"
        "2️⃣ **Как запустить:**\n"
        "• Нажмите **«🚀 Получить прокси»** здесь.\n"
        "• Скопируйте текст из файла.\n"
        "• В приложении нажмите **«Новый профиль» (+)** -> **«Из буфера»**.\n"
        "• Нажмите круглую кнопку в центре.\n\n"
        "✅ **Все готово!**"
    )
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=get_main_keyboard())

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    await notify_admin(message.from_user, "Смотрит статус")
    await message.answer(f"🤖 **Статус:** Ок\n🕒 **Обновлено:** `{last_update_time}`", parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(F.text == "🚀 Получить прокси")
@dp.message(Command("test"))
async def manual_test(message: types.Message):
    save_user(message.from_user.id)
    await notify_admin(message.from_user, "Запросил файл")
    proxies = await get_proxies()
    if proxies:
        caption = f"📄 Ваши настройки!\n🕒 Актуально на: {last_update_time}"
        file_data = proxies.encode('utf-8')
        await bot.send_document(message.chat.id, BufferedInputFile(file_data, filename="proxies.txt"), caption=caption, reply_markup=get_main_keyboard())
    else:
        await message.answer("❌ Ошибка связи.", reply_markup=get_main_keyboard())

# --- ЦИКЛ МОНИТОРИНГА ---
async def check_proxies_loop():
    global last_hash, last_update_time
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                new_time_str = now.strftime("%H:%M:%S (%d.%m.%Y)")
                if last_hash != "start_node":
                    last_update_time = new_time_str
                    msg = f"🔔 **НОВЫЕ ПРОКСИ!**\nНажмите «🚀 Получить прокси»."
                    for uid in get_all_users():
                        try:
                            await bot.send_message(uid, msg, parse_mode="Markdown", reply_markup=get_main_keyboard())
                            await asyncio.sleep(0.1)
                        except: continue
                else: last_update_time = new_time_str
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot Alive"))
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', int(os.getenv("PORT", 10000))).start()

async def main():
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
