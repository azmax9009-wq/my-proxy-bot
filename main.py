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

# Глобальные переменные для отслеживания изменений
last_hash = "start_node"
last_update_time = "Ожидание..."

# --- УТИЛИТЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ---
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

async def check_host(host, port):
    try:
        conn = asyncio.open_connection(host, int(port))
        reader, writer = await asyncio.wait_for(conn, timeout=2.0)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

# --- КЛАВИАТУРА ---
def get_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Ваш персональный VPN-центр готов!**\n\n"
        "Я буду автоматически присылать уведомления, если прокси обновятся.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **КАК ПОДКЛЮЧИТЬ VPN?**\n\n"
        "**Шаг 1:** Установите приложение **Hiddify**.\n"
        "**Шаг 2:** Нажмите кнопку **'🚀 ПОЛУЧИТЬ НАСТРОЙКИ'**.\n"
        "**Шаг 3:** Скопируйте текст из файла и добавьте в приложение через '+' (из буфера)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/hiddify-next/id6473777529")]
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
                caption = f"✅ **Конфигурация готова!**\n🌍 Узлов: {total}\n🕒 Обновлено: {last_update_time}"
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(content.encode(), filename="proxies.txt"), 
                    caption=caption, parse_mode="Markdown"
                )

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    hosts = re.findall(r'@([\w\.-]+):(\d+)', content)
    active = len(hosts) # Упрощенно для примера
    await message.answer(f"🟢 Серверов в базе: {len(hosts)}\n🕒 Последняя проверка: {last_update_time}", parse_mode="Markdown")

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in get_all_users():
        try: await bot.send_message(uid, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{text}")
        except: pass

# --- СИСТЕМНЫЙ ЦИКЛ ПРОВЕРКИ ---
async def check_github_loop():
    global last_hash, last_update_time
    print("Запуск фоновой проверки GitHub...")
    
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
                            
                            # Если это не самый первый запуск — уведомляем всех
                            if last_hash != "start_node":
                                for uid in get_all_users():
                                    try: 
                                        await bot.send_message(uid, "🔔 **Обновление!** На GitHub появились новые прокси. Нажмите кнопку получения настроек.")
                                    except: pass
                            
                            last_hash = new_hash
                            print(f"Обновление зафиксировано: {last_update_time}")
        except Exception as e:
            print(f"Ошибка проверки: {e}")
            
        await asyncio.sleep(60)

# --- WEB СЕРВЕР (ДЛЯ RENDER) ---
async def handle(request): return web.Response(text="Bot is running")

async def main():
    # 1. Запуск веб-заглушки
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    # 2. Очистка старых обновлений (чтобы не тупил при запуске)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Уведомление владельца о запуске (вместо ручного /start)
    try:
        await bot.send_message(USER_ID, "✅ **Бот успешно обновлен и запущен!**\nТеперь я автоматически слежу за GitHub.")
    except: pass
    
    # 4. Запуск проверки GitHub в фоне
    asyncio.create_task(check_github_loop())
    
    # 5. Старт прослушивания команд
    print("Бот полностью запущен.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
