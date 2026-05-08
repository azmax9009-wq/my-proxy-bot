import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'
USERS_FILE = "users_list.txt"

# Картинки
START_PIC = "https://w.forfun.com/fetch/1f/1f81d113426e2a149a4a755d506927d1.jpeg"
ADMIN_PIC = "https://img.goodfon.ru/original/1920x1080/7/da/mariya-s-shlemom-art-kiberpank-pogranichnik-cyberpunk.jpg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

LAST_FILE_HASH = None

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---

def get_all_users():
    """Получает список всех ID из файла"""
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def save_user(user_id):
    """Сохраняет нового пользователя"""
    users = get_all_users()
    if str(user_id) not in users:
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")
        return True
    return False

async def startup_notification():
    """Рассылка сообщения о том, что бот обновился/запустился"""
    users = get_all_users()
    for uid in users:
        try:
            await bot.send_message(uid, "⚡️ **Бот успешно обновлен и запущен!**\nТеперь я снова на связи и слежу за новыми прокси.")
            await asyncio.sleep(0.05)
        except:
            pass

def clean_for_iphone(text):
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]
    return "\n".join(lines)

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    kb = [[KeyboardButton(text="📱 Получить Конфиг")],
          [KeyboardButton(text="📸 QR-Код"), KeyboardButton(text="📊 Статус")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- МОНИТОРИНГ GITHUB ---

async def auto_update_checker():
    global LAST_FILE_HASH
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        current_hash = hashlib.md5(content.encode()).hexdigest()
                        if LAST_FILE_HASH is not None and current_hash != LAST_FILE_HASH:
                            LAST_FILE_HASH = current_hash
                            await broadcast_new_proxies(content)
                        else:
                            LAST_FILE_HASH = current_hash
        except: pass
        await asyncio.sleep(60) # Проверка каждую минуту

async def broadcast_new_proxies(content):
    users = get_all_users()
    iphone_data = clean_for_iphone(content).encode()
    for uid in users:
        try:
            await bot.send_message(uid, "🆕 **На GitHub появились новые прокси!**\nЛови свежий файл:")
            await bot.send_document(uid, BufferedInputFile(iphone_data, filename="New_Configs.txt"))
            await asyncio.sleep(0.05)
        except: pass

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_photo(message.chat.id, START_PIC, 
                         caption="🔥 **Happ VPN Online**\n\nЯ сохраню твой ID и буду присылать обновления автоматически!", 
                         reply_markup=get_main_kb(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def send_config(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                data = clean_for_iphone(await r.text())
                await bot.send_document(message.chat.id, BufferedInputFile(data.encode(), filename="Configs.txt"), caption="🍏 Твой конфиг")

@dp.message(F.text == "📊 Статус")
async def status_check(message: types.Message):
    await message.answer("🛰 Система: `Online`\n📡 Авто-рассылка: `Включена`", parse_mode="Markdown")

# --- ЗАПУСК ---

async def handle_web(request): return web.Response(text="Running")

async def main():
    # 1. Запускаем фоновую слежку за GitHub
    asyncio.create_task(auto_update_checker())
    
    # 2. Делаем рассылку "Бот обновлен" всем, кто в базе
    asyncio.create_task(startup_notification())

    # 3. Настройка веб-сервера (для деплоя)
    app = web.Application(); app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        print("Bot off")