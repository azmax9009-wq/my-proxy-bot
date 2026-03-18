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

# --- АДМИН ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != USER_ID: return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Список ID (txt)", callback_data="admin_get_users")],
        [InlineKeyboardButton(text="🔄 Обновить базу сейчас", callback_data="admin_force_update")]
    ])
    
    await message.answer(
        f"👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**\n\n"
        f"👥 Юзеров в базе: **{len(get_all_users())}**\n"
        f"🕒 Последняя проверка: `{last_update_time}`\n"
        f"🔗 [Твой GitHub]({PROXY_URL})",
        reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True
    )

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callbacks(callback: CallbackQuery):
    if callback.from_user.id != USER_ID: return
    
    if callback.data == "admin_broadcast":
        await callback.message.answer("Чтобы сделать рассылку, используй команду:\n\n`/broadcast Твой текст`", parse_mode="Markdown")
    
    elif callback.data == "admin_get_users":
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "rb") as f:
                file_content = f.read()
            await callback.message.answer_document(BufferedInputFile(file_content, filename="users.txt"), caption="📊 Полный список пользователей")
    
    elif callback.data == "admin_force_update":
        await callback.message.answer("🔄 Проверяю GitHub...")
        await check_github_now()
        await callback.message.answer(f"✅ Готово! Статус: {last_update_time}")
    
    await callback.answer()

# --- ОСНОВНЫЕ КНОПКИ ---
def get_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer("✅ **Бот запущен и готов к работе!**", reply_markup=get_kb(), parse_mode="Markdown")

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    
    hosts = re.findall(r'@([\w\.-]+):(\d+)', content)
    tasks = [check_host(h, p) for h, p in hosts] # Проверяем ВСЕ
    results = await asyncio.gather(*tasks)
    active = results.count(True)
    
    await message.answer(
        f"🖥 **МОНИТОРИНГ**\n\n"
        f"📡 Доступно: `{active} из {len(hosts)}` серверов\n"
        f"📶 Стабильность: **{int((active/len(hosts))*100) if hosts else 0}%**\n"
        f"🕒 Данные от: `{last_update_time}`", 
        parse_mode="Markdown"
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
                    f"✅ **Настройки готовы!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Всего узлов: **{total}**\n"
                    f"🕒 Обновлено: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━"
                )
                await bot.send_document(message.chat.id, BufferedInputFile(content.encode(), filename="proxies.txt"), caption=caption, parse_mode="Markdown")

@dp.message(F.text == "⚡ Скорость")
async def speed(message: types.Message):
    await message.answer("🚀 Проверь скорость тут: [Fast.com](https://fast.com/ru/)", parse_mode="Markdown")

@dp.message(F.text == "📖 Инструкция")
async def instr(message: types.Message):
    await message.answer("1. Нажми 'Получить настройки'\n2. Скопируй текст из файла\n3. В Hiddify: + -> Из буфера")

# --- СИСТЕМНЫЕ ФУНКЦИИ ---
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
                                try: await bot.send_message(uid, "🔔 Настройки на GitHub обновились! Скачайте свежий файл."); await asyncio.sleep(0.05)
                                except: pass
                        last_hash = h
    except: pass

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in get_all_users():
        try: await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{text}"); await asyncio.sleep(0.05)
        except: pass

async def check_loop():
    while True:
        await check_github_now()
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    asyncio.create_task(check_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
