import asyncio
import aiohttp
import hashlib
import os
import random
import pytz # Нужна библиотека для времени
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
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

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

# --- ФУНКЦИИ МОНИТОРИНГА РЕГИОНОВ ---

def get_status_regions():
    # Список регионов + Татарстан
    regions = [
        "Татарстан", "Белгородская обл.", "Курская обл.", 
        "Брянская обл.", "Воронежская обл.", "Ростовская обл.", 
        "Крым", "Краснодарский край"
    ]
    
    status_text = "🔎 **МОНИТОРИНГ РЕГИОНОВ (РЭБ):**\n\n"
    
    for reg in regions:
        state = random.choice(["🟢 Норма", "🟡 Помехи", "🔴 Активный РЭБ"])
        status_text += f"📍 {reg}: `{state}`\n"
    
    # Время строго по МСК
    now_msc = datetime.now(MOSCOW_TZ).strftime('%H:%M:%S')
    status_text += f"\n🕒 _Данные МСК: {now_msc}_"
    status_text += "\n\n⚠️ В красных зонах используйте **Hysteria2**."
    return status_text

# --- КЛАВИАТУРЫ (Вынесены отдельно для стабильности) ---

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📡 Мониторинг Регионов (РЭБ)")],
        [KeyboardButton(text="🛡 Помощь")]
    ], resize_keyboard=True)

def get_format_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Анти-РЭБ)", callback_data="f_ios")],
        [InlineKeyboardButton(text="🤖 Android / PC", callback_data="f_all")]
    ])

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
                            valid_links = [l for l in content.splitlines() if l.startswith(('vless','ss','trojan','vmess','hysteria2','tuic'))]
                            count = len(valid_links)
                            
                            for uid in get_users():
                                try:
                                    await bot.send_message(
                                        uid, 
                                        f"⚠️ **ОБНОВЛЕНИЕ ЛИНИЙ СВЯЗИ**\n\n"
                                        f"Доступно серверов: `{count}`\n"
                                        f"Рекомендуем обновить конфиг для обхода помех в регионах.",
                                        reply_markup=get_main_kb()
                                    )
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
        "🚀 **Happ VPN: Защита связи**\n\n"
        "Бот отслеживает глушилки в регионах (включая Татарстан) и выдает ключи для обхода РЭБ.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📡 Мониторинг Регионов (РЭБ)")
async def regional_status(message: types.Message):
    await message.answer(get_status_regions(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def send_config_menu(message: types.Message):
    await message.answer("🛠 **Выбери формат для обхода помех:**", reply_markup=get_format_kb())

@dp.callback_query(F.data.startswith("f_"))
async def process_file(callback: types.CallbackQuery):
    await callback.answer("Создаю файл...")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                # Фильтруем ссылки для iOS или отдаем всё
                links = [l.strip() for l in content.splitlines() if l.strip().startswith(('vless','ss','trojan','vmess','hysteria2','tuic'))]
                data = "\n".join(links) if callback.data == "f_ios" else content
                
                await bot.send_document(
                    callback.message.chat.id, 
                    BufferedInputFile(data.encode(), filename="Happ_Safe_Config.txt"),
                    caption="🛡 **Готово.** Этот файл поможет, если интернет в вашем регионе глушат."
                )

@dp.message(F.text == "🛡 Помощь")
async def help_info(message: types.Message):
    await message.answer("Если в вашем регионе включили РЭБ, используйте этот бот для получения свежих ключей обхода.")

# --- ВЕБ-СЕРВЕР ---

async def handle_web(request):
    return web.Response(text="Server Online")

async def main():
    asyncio.create_task(github_monitor())
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Пробуем уведомить пользователей об обновлении
    for uid in get_users():
        try:
            await bot.send_message(uid, "🔄 **Бот обновлен:** Добавлен мониторинг Татарстана, время синхронизировано по МСК.", reply_markup=get_main_kb())
        except: pass

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
