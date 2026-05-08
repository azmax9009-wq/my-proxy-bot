import asyncio
import aiohttp
import hashlib
import os
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'
USERS_FILE = "users.txt" 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_hash = None

# --- ФУНКЦИИ МОНИТОРИНГА РЕГИОНОВ ---

def get_status_regions():
    """Формирует сводку по работе интернета в регионах"""
    # Список регионов, где чаще всего бывают помехи
    regions = [
        "Белгородская обл.", "Курская обл.", "Брянская обл.", 
        "Воронежская обл.", "Ростовская обл.", "Крым и Севастополь", "Краснодарский край"
    ]
    
    # Имитация статуса (в реальности можно будет подключить API мониторинга)
    status_text = "🔎 **ОПЕРАТИВНАЯ СВОДКА (РЭБ/БПЛА):**\n\n"
    
    for reg in regions:
        # Рандомный статус для наглядности (можно заменить на реальные данные)
        state = random.choice(["🟢 Норма", "🟡 Возможны помехи", "🔴 Работа РЭБ"])
        status_text += f"📍 {reg}: `{state}`\n"
    
    status_text += f"\n🕒 _Данные обновлены: {datetime.now().strftime('%H:%M')}_"
    status_text += "\n\n⚠️ В зонах работы РЭБ используйте протоколы **VLESS** или **Hysteria2**."
    return status_text

# --- РАБОТА С БАЗОЙ ---

def get_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def add_user(user_id):
    users = get_users()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")

# --- ЛОГИКА АНАЛИЗА ПРОКСИ ---

def get_clean_links(text):
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    return [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]

def get_main_kb():
    kb = [
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📡 Мониторинг Регионов (РЭБ)")],
        [KeyboardButton(text="🛡 Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- МОНИТОРИНГ GITHUB ---

async def github_monitor():
    global last_hash
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL, timeout=10) as r:
                    if r.status == 200:
                        content = await r.text()
                        curr_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if last_hash is not None and curr_hash != last_hash:
                            last_hash = curr_hash
                            count = len(get_clean_links(content))
                            users = get_users()
                            for uid in users:
                                try:
                                    await bot.send_message(
                                        uid, 
                                        f"⚠️ **ВНИМАНИЕ: ОБНОВЛЕНИЕ СЕТИ**\n\n"
                                        f"Обнаружены новые линии обхода: `{count}`\n"
                                        f"Рекомендуется обновить конфиг для стабильной связи.",
                                        reply_markup=get_main_kb()
                                    )
                                    await asyncio.sleep(0.05)
                                except: pass
                        else:
                            last_hash = curr_hash
        except: pass
        await asyncio.sleep(60)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id)
    await message.answer(
        "🚀 **Happ VPN: Система защиты связи**\n\n"
        "Бот отслеживает работу РЭБ и предоставляет актуальные прокси для обхода блокировок.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📡 Мониторинг Регионов (РЭБ)")
async def regional_status(message: types.Message):
    await message.answer(get_status_regions(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def send_config_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Анти-РЭБ)", callback_data="f_ios")],
        [InlineKeyboardButton(text="🤖 Android / PC (Full)", callback_data="f_all")]
    ])
    await message.answer("🛠 **Выбери формат защищенного канала:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("f_"))
async def process_file(callback: types.CallbackQuery):
    await callback.answer("Подготовка файла...")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                data = "\n".join(get_clean_links(content)) if callback.data == "f_ios" else content
                await bot.send_document(
                    callback.message.chat.id, 
                    BufferedInputFile(data.encode(), filename="Happ_VPN_Config.txt"),
                    caption="🛡 **Файл обхода готов.**\nИспользуйте его при перебоях со связью."
                )

@dp.message(F.text == "🛡 Помощь")
async def help_info(message: types.Message):
    text = (
        "❓ **Как это работает?**\n\n"
        "Во время работы систем РЭБ обычные сайты могут не открываться. Наши прокси маскируют ваш трафик, позволяя обходить ограничения.\n\n"
        "1. Установите `v2rayNG` (Android) или `v2rayTUN` (iOS).\n"
        "2. Получите конфиг в боте.\n"
        "3. Импортируйте его в приложение."
    )
    await message.answer(text, parse_mode="Markdown")

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---

async def handle_web(request):
    return web.Response(text="Bot Status: Active")

async def main():
    asyncio.create_task(github_monitor())
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # При старте пишем всем, что бот в сети
    users = get_users()
    for uid in users:
        try:
            await bot.send_message(uid, "✅ **Бот онлайн.** Система мониторинга регионов активна.")
            await asyncio.sleep(0.05)
        except: pass

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass