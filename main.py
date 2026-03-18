import asyncio
import aiohttp
import hashlib
import os
import time
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

# --- ФУНКЦИИ ПРОВЕРКИ ---
async def check_link_latency():
    """Проверяет, как быстро отвечает ссылка с прокси"""
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROXY_URL, timeout=5) as resp:
                if resp.status == 200:
                    latency = int((time.time() - start) * 1000)
                    if latency < 300: return f"🟢 Отлично ({latency}ms)"
                    if latency < 800: return f"🟡 Средне ({latency}ms)"
                    return f"🔴 Медленно ({latency}ms)"
    except: pass
    return "⚪ Офлайн"

def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    with open(USERS_FILE, "r") as f: return [int(l.strip()) for l in f if l.strip().isdigit()]

def save_user(user_id):
    u_id = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write(u_id + "\n")
        return
    with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if u_id not in users:
        with open(USERS_FILE, "a") as f: f.write(u_id + "\n")

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="📊 Статус и Пинг"), KeyboardButton(text="⚡ Скорость")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("👋 **Бот готов к работе!**\nИспользуйте меню для получения прокси.", reply_markup=get_main_keyboard())

@dp.message(F.text == "📊 Статус и Пинг")
async def status_check(message: types.Message):
    ping_status = await check_link_latency()
    status_text = (
        f"🖥 **МОНИТОРИНГ СЕТИ**\n\n"
        f"🔗 **Доступность узла:** {ping_status}\n"
        f"📅 **Обновление базы:** `{last_update_time}`\n\n"
        f"💡 _Примечание: Этот пинг показывает связь бота с сервером. Ваш личный пинг проверяйте в приложении Hiddify._"
    )
    await message.answer(status_text, parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_proxies(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "upload_document")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as resp:
            if resp.status == 200:
                content = await resp.text()
                # Считаем количество серверов в файле
                count = len(content.strip().split('\n'))
                ping_info = await check_link_latency()
                
                caption = (
                    f"✅ **Настройки получены!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Найдено серверов: **{count}**\n"
                    f"📡 Пинг (серверный): {ping_info}\n"
                    f"🕒 Актуально на: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👇 Скопируйте текст из файла ниже:"
                )
                
                file_data = content.encode('utf-8')
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(file_data, filename="proxies.txt"), 
                    caption=caption,
                    parse_mode="Markdown"
                )

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return await message.answer("Введите текст.")
    for uid in get_all_users():
        try: await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{text}"); await asyncio.sleep(0.1)
        except: pass
    await message.answer("✅ Рассылка завершена.")

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **КАК ПРОВЕРИТЬ ПИНГ В ПРИЛОЖЕНИИ:**\n\n"
        "1. Зайдите в Hiddify.\n"
        "2. Нажмите на иконку молнии ⚡ в углу экрана.\n"
        "3. Приложение проверит **ваш реальный пинг** до каждого сервера.\n"
        "4. Выбирайте тот, где цифра меньше (например, 60ms лучше, чем 150ms)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/hiddify-next/id6473777529")]
    ])
    await message.answer(text, reply_markup=kb)

# --- LOOP & WEB ---
async def check_proxies_loop():
    global last_hash, last_update_time
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(PROXY_URL) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        curr_hash = hashlib.md5(content.encode()).hexdigest()
                        if curr_hash != last_hash:
                            now = datetime.now(pytz.timezone('Europe/Moscow'))
                            last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                            if last_hash != "start_node":
                                for uid in get_all_users():
                                    try: await bot.send_message(uid, "🔔 **Настройки обновились!** Заберите новый файл кнопкой в меню."); await asyncio.sleep(0.1)
                                    except: pass
                            last_hash = curr_hash
            except: pass
        await asyncio.sleep(CHECK_INTERVAL)

async def handle(request): return web.Response(text="Online")

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
