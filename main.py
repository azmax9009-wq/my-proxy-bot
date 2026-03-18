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
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

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
        with open(USERS_FILE, "r") as f: return [int(l.strip()) for l in f if l.strip().isdigit()]
    except: return [USER_ID]

async def notify_admin(user: types.User, action: str):
    if user.id != USER_ID:
        try: await bot.send_message(USER_ID, f"👤 **{user.full_name}**: {action}", parse_mode="Markdown")
        except: pass

def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 Получить прокси")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="ℹ️ О боте")]
    ], resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=15) as resp:
                if resp.status == 200: return (await resp.text()).strip()
        except: pass
    return None

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await notify_admin(message.from_user, "запустил бота")
    await message.answer("👋 Привет! Используй кнопки ниже:", reply_markup=get_main_keyboard())

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    await notify_admin(message.from_user, "открыл инструкцию")
    help_text = "📖 **Инструкция:**\n1. Ставим Hiddify ([Android](https://play.google.com/store/apps/details?id=app.hiddify.com) / [iOS](https://apps.apple.com/us/app/hiddify-next/id6473777529))\n2. Жмем «🚀 Получить прокси»\n3. Копируем текст из файла и вставляем в Hiddify через «+»."
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    await message.answer(f"🤖 Статус: ОК\n🕒 Обновлено: {last_update_time}")

@dp.message(F.text == "🚀 Получить прокси")
@dp.message(Command("test"))
async def manual_test(message: types.Message):
    save_user(message.from_user.id)
    proxies = await get_proxies()
    if proxies:
        file_data = proxies.encode('utf-8')
        await bot.send_document(message.chat.id, BufferedInputFile(file_data, filename="proxies.txt"), caption=f"🕒 {last_update_time}")
    else:
        await message.answer("❌ Ошибка загрузки данных.")

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
                    msg = "🔔 Появились новые прокси!"
                    for uid in get_all_users():
                        try: await bot.send_message(uid, msg, reply_markup=get_main_keyboard()); await asyncio.sleep(0.1)
                        except: pass
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def handle(request):
    return web.Response(text="Bot is Alive")

async def main():
    # Важное исправление для Render:
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    # Очистка конфликтов
    await bot.delete_webhook(drop_pending_updates=True)
    
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
