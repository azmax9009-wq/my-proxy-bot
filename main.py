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
    with open(USERS_FILE, "r") as f: 
        return [int(l.strip()) for l in f if l.strip().isdigit()]

def save_user(user_id):
    u_id = str(user_id)
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if u_id not in users:
        with open(USERS_FILE, "a") as f: f.write(u_id + "\n")

async def check_host(host, port):
    try:
        conn = asyncio.open_connection(host, int(port))
        reader, writer = await asyncio.wait_for(conn, timeout=2.0)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

# --- ОБРАБОТЧИКИ КНОПОК ---
def get_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Привет! Я бот для получения рабочих VPN-настроек.**\n\n"
        "Жми кнопку ниже, чтобы получить файл или прочитать инструкцию.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "upload_document")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                total = len(re.findall(r'vless://', content))
                caption = (
                    f"✅ **Ваш файл готов!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Серверов в списке: **{total}**\n"
                    f"🕒 Актуально на: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"Скопируйте всё содержимое файла и вставьте в приложение."
                )
                await bot.send_document(message.chat.id, BufferedInputFile(content.encode(), filename="proxies.txt"), caption=caption, parse_mode="Markdown")

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    
    hosts = re.findall(r'@([\w\.-]+):(\d+)', content)
    tasks = [check_host(h, p) for h, p in hosts]
    results = await asyncio.gather(*tasks)
    active = results.count(True)
    
    await message.answer(
        f"🖥 **МОНИТОРИНГ**\n\n"
        f"📡 Живых узлов: `{active} из {len(hosts)}`\n"
        f"📈 Стабильность базы: **{int((active/len(hosts))*100) if hosts else 0}%**\n"
        f"🕒 Последняя синхронизация: `{last_update_time}`", 
        parse_mode="Markdown"
    )

@dp.message(F.text == "⚡ Скорость")
async def speed_test_btn(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать тест скорости", url="https://fast.com/ru/")]
    ])
    await message.answer("📏 Нажмите кнопку ниже, чтобы проверить скорость вашего VPN соединения:", reply_markup=kb)

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **ИНСТРУКЦИЯ ПО ПОДКЛЮЧЕНИЮ**\n\n"
        "1️⃣ **Скачайте приложение Hiddify:**\n"
        "• [Android (Play Store)](https://play.google.com/store/apps/details?id=app.hiddify.com)\n"
        "• [iOS (App Store)](https://apps.apple.com/us/app/hiddify/id6473760000)\n"
        "• [Windows / PC](https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Windows-Setup-x64.exe)\n\n"
        "2️⃣ **Получите настройки:**\n"
        "Нажмите кнопку '🚀 ПОЛУЧИТЬ НАСТРОЙКИ' и скачайте файл.\n\n"
        "3️⃣ **Импортируйте:**\n"
        "Откройте файл, скопируйте весь текст. В приложении Hiddify нажмите кнопку **'+' (Новый профиль)** -> **'Из буфера обмена'**.\n\n"
        "4️⃣ **Подключитесь:**\n"
        "Нажмите на центральную кнопку подключения. Готово!"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

# --- АДМИНКА ---
@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != USER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Скачать ID", callback_data="admin_get_users")]
    ])
    await message.answer(f"👑 Админка\nЮзеров: {len(get_all_users())}", reply_markup=kb)

@dp.callback_query(F.data.startswith("admin_"))
async def admin_cb(callback: CallbackQuery):
    if callback.from_user.id != USER_ID: return
    if callback.data == "admin_broadcast":
        await callback.message.answer("Пиши: `/broadcast Твой текст`", parse_mode="Markdown")
    elif callback.data == "admin_get_users":
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "rb") as f:
                await callback.message.answer_document(BufferedInputFile(f.read(), filename="users.txt"))
    await callback.answer()

@dp.message(Command("broadcast"))
async def broadcast_cmd(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in get_all_users():
        try: await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{text}"); await asyncio.sleep(0.05)
        except: pass

# --- СИСТЕМНЫЙ ЦИКЛ ---
async def check_github_now():
    global last_hash, last_update_time
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    c = await r.text()
                    h = hashlib.md5(c.encode()).hexdigest()
                    if h != last_hash:
                        now = datetime.now(pytz.timezone('Europe/Moscow'))
                        last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                        if last_hash != "start_node":
                            for uid in get_all_users():
                                try: await bot.send_message(uid, "🔔 Настройки обновлены!"); await asyncio.sleep(0.05)
                                except: pass
                        last_hash = h
    except: pass

async def check_loop():
    while True:
        await check_github_now()
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="Bot Active")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(check_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
