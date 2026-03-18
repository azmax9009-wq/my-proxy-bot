import asyncio
import aiohttp
import hashlib
import os
import time
import re
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

# --- МОЩНЫЙ СКАНЕР ВСЕХ СЕРВЕРОВ ---

async def check_single_host(host, port):
    """Проверяет один конкретный сервер"""
    start = time.time()
    try:
        # Пытаемся быстро открыть TCP соединение
        conn = asyncio.open_connection(host, int(port))
        reader, writer = await asyncio.wait_for(conn, timeout=2.0)
        writer.close()
        await writer.wait_closed()
        return int((time.time() - start) * 1000)
    except:
        return None

async def scan_all_proxies(config_text):
    """Парсит ВСЕ ссылки и проверяет каждый сервер одновременно"""
    # Ищем все пары хост:порт в формате vless/vmessage/etc
    hosts = re.findall(r'@([\w\.-]+):(\d+)', config_text)
    if not hosts:
        return "❌ Серверы не найдены", 0
    
    # Создаем задачи на проверку для ВСЕХ найденных серверов
    tasks = [check_single_host(h, p) for h, p in hosts]
    results = await asyncio.gather(*tasks)
    
    latencies = [r for r in results if r is not None]
    active_count = len(latencies)
    dead_count = len(hosts) - active_count
    
    if active_count > 0:
        avg_ping = sum(latencies) // active_count
        status = f"🟢 {active_count} живых, 🔴 {dead_count} спит\n📡 Ср. пинг: {avg_ping}ms"
    else:
        status = f"🔴 Все {len(hosts)} серверов недоступны"
        
    return status, len(hosts)

# --- БАЗОВАЯ ЛОГИКА ---

def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    try:
        with open(USERS_FILE, "r") as f: return [int(l.strip()) for l in f if l.strip().isdigit()]
    except: return [USER_ID]

def save_user(user_id):
    u_id = str(user_id)
    try:
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as fr: users = fr.read().splitlines()
        if u_id not in users:
            with open(USERS_FILE, "a") as f: f.write(u_id + "\n")
    except: pass

def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="⚡ Скорость")]
    ], resize_keyboard=True)

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "upload_document")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                # Запускаем полную проверку всех серверов
                ping_report, total = await scan_all_proxies(content)
                
                caption = (
                    f"✅ **Конфигурация готова!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Всего серверов: **{total}**\n"
                    f"📊 Состояние:\n{ping_report}\n"
                    f"🕒 Обновлено: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💡 _Скопируйте файл в приложение Hiddify._"
                )
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(content.encode(), filename="proxies.txt"), 
                    caption=caption, 
                    parse_mode="Markdown"
                )

@dp.message(F.text == "📊 Статус")
async def status_msg(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    
    report, _ = await scan_all_proxies(content)
    await message.answer(f"📊 **ОТЧЕТ ПО СЕТИ:**\n\n{report}\n\n🕒 Данные на: {last_update_time}", parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in get_all_users():
        try: await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{text}"); await asyncio.sleep(0.1)
        except: pass

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("👋 Бот активен и готов раздавать прокси!", reply_markup=get_main_keyboard())

# --- СЕРВЕР И МОНИТОРИНГ ---
async def check_loop():
    global last_hash, last_update_time
    while True:
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
                                    try: await bot.send_message(uid, "🔔 Настройки на GitHub обновились! Скачайте свежий файл."); await asyncio.sleep(0.1)
                                    except: pass
                            last_hash = h
        except: pass
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="Bot is Live")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
