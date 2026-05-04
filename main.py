import asyncio
import aiohttp
import hashlib
import os
import time
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361
TARGET_USERS = [1201378326, 1180353475, 6723386873, 5209666874, 8208699361]
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = ""
last_update_time = "Ожидание..."
session = None

def get_iphone_clean_content(raw_text):
    """
    СПЕЦИАЛЬНО ДЛЯ IPHONE:
    Оставляет только строки, начинающиеся на vless, trojan, ss, vmess и т.д.
    Все остальное (текст, решетки, даты) — удаляется под ноль.
    """
    valid_protocols = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    clean_lines = []
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith(valid_protocols):
            clean_lines.append(line)
    return "\n".join(clean_lines)

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Для iPhone (Happ)")], # Новая кнопка
        [KeyboardButton(text="🚀 Обычный конфиг")],
        [KeyboardButton(text="📊 Статус"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Бот Happ VPN запущен.\n\n"
        "Если у тебя iPhone — используй первую кнопку, чтобы импорт прошел без ошибок.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📱 Для iPhone (Happ)")
async def send_iphone_file(message: types.Message):
    global session
    try:
        async with session.get(PROXY_URL, timeout=15) as r:
            if r.status == 200:
                raw_data = await r.text()
                # Жесткая очистка только под протоколы
                clean_data = get_iphone_clean_content(raw_data)
                
                if not clean_data:
                    await message.answer("❌ На GitHub не найдено рабочих ссылок.")
                    return

                file_bytes = clean_data.encode('utf-8')
                await message.answer_document(
                    BufferedInputFile(file_bytes, filename="iPhone_Happ_Fix.txt"),
                    caption=f"🍏 **Файл для iPhone готов!**\n\nЯ удалил все комментарии и заголовок. Просто скопируй содержимое файла и вставь в Happ.\n🕒 База от: {last_update_time}",
                    parse_mode="Markdown"
                )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(F.text == "🚀 Обычный конфиг")
async def send_normal_file(message: types.Message):
    global session
    try:
        async with session.get(PROXY_URL, timeout=15) as r:
            if r.status == 200:
                file_bytes = (await r.read())
                await message.answer_document(
                    BufferedInputFile(file_bytes, filename="Standard_Config.txt"),
                    caption=f"📄 **Обычный конфиг (с описанием)**\n🕒 Обновлено: {last_update_time}"
                )
    except:
        await message.answer("❌ Ошибка загрузки.")

@dp.message(F.text == "📊 Статус")
async def status_check(message: types.Message):
    await message.answer(f"🛰 Бот активен\n🕒 Последнее обновление: {last_update_time}")

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    await message.answer(
        "📖 **Для владельцев iPhone:**\n"
        "1. Нажми кнопку '📱 Для iPhone'.\n"
        "2. Открой полученный файл.\n"
        "3. Скопируй весь текст.\n"
        "4. В приложении Happ нажми '+' -> 'Add from Clipboard'.",
        parse_mode="Markdown"
    )

# --- БЛОК ДЛЯ RENDER И ОБНОВЛЕНИЙ ---
async def check_updates():
    global last_hash, last_update_time, session
    while True:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    text = await r.text()
                    new_hash = hashlib.md5(text.encode()).hexdigest()
                    if new_hash != last_hash:
                        last_hash = new_hash
                        last_update_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%d.%m %H:%M")
                        if last_hash != "":
                            for user_id in TARGET_USERS:
                                try: await bot.send_message(user_id, "🔄 **Обновление базы!**\nСкачайте новый файл.")
                                except: pass
        except: pass
        await asyncio.sleep(60)

async def handle_web(request): return web.Response(text="Bot is running")

async def main():
    global session
    session = aiohttp.ClientSession()
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_updates())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
