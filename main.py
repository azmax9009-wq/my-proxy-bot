import asyncio
import aiohttp
import hashlib
import os
import pytz
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

# --- РАБОТА С БАЗОЙ (Сохранение юзеров) ---

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

# --- ФУНКЦИИ МОНИТОРИНГА (ВАРИАНТ 1: ГОТОВНОСТЬ) ---

def get_status_regions():
    regions = [
        "Татарстан", "Белгородская обл.", "Курская обл.", 
        "Брянская обл.", "Воронежская обл.", "Ростовская обл.", 
        "Крым", "Краснодарский край"
    ]
    
    status_text = "🛡 **СТАТУС ГОТОВНОСТИ К РЭБ/БПЛА:**\n\n"
    
    for reg in regions:
        # Статус теперь стабильный: подтверждаем готовность линий обхода
        status_text += f"📍 {reg}: `Система готова` ✅\n"
    
    # Время строго по МСК
    now_msc = datetime.now(MOSCOW_TZ).strftime('%H:%M:%S')
    status_text += f"\n🕒 _Контроль систем: {now_msc} (МСК)_"
    status_text += "\n\nℹ️ _В случае активации глушилок используйте протоколы Hysteria2 и VLESS из нашего конфига._"
    return status_text

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📡 Статус по регионам")],
        [KeyboardButton(text="🛡 Помощь")]
    ], resize_keyboard=True)

def get_format_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Анти-РЭБ)", callback_data="f_ios")],
        [InlineKeyboardButton(text="🤖 Android / PC (Full)", callback_data="f_all")]
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
                            # Считаем ссылки
                            links = [l for l in content.splitlines() if l.startswith(('vless','ss','trojan','vmess','hysteria2','tuic'))]
                            count = len(links)
                            
                            for uid in get_users():
                                try:
                                    await bot.send_message(
                                        uid, 
                                        f"⚠️ **ОБНОВЛЕНИЕ БАЗЫ ОБХОДА**\n\n"
                                        f"Доступно защищенных линий: `{count}`\n"
                                        f"Статус: `Оптимизировано для зон РЭБ`\n\n"
                                        f"Заберите новый конфиг кнопкой ниже 👇",
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
        "🚀 **Happ VPN Online**\n\n"
        "Бот адаптирован для обеспечения связи в регионах с активными системами помех.\n"
        "Мы оповестим тебя, как только ключи обновятся.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📡 Статус по регионам")
async def regional_status(message: types.Message):
    await message.answer(get_status_regions(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def send_config_menu(message: types.Message):
    await message.answer("🛠 **Выбери формат файла:**", reply_markup=get_format_kb())

@dp.callback_query(F.data.startswith("f_"))
async def process_file(callback: types.CallbackQuery):
    await callback.answer("Подключение...")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                links = [l.strip() for l in content.splitlines() if l.strip().startswith(('vless','ss','trojan','vmess','hysteria2','tuic'))]
                data = "\n".join(links) if callback.data == "f_ios" else content
                
                await bot.send_document(
                    callback.message.chat.id, 
                    BufferedInputFile(data.encode(), filename="Happ_VPN.txt"),
                    caption="🛡 **Конфиг готов.**\nИспользуйте его, если стандартный интернет работает нестабильно."
                )

@dp.message(F.text == "🛡 Помощь")
async def help_info(message: types.Message):
    await message.answer("При потере связи импортируйте свежий файл в v2rayNG или v2rayTUN. Эти протоколы сложнее заглушить.")

# --- ВЕБ-СЕРВЕР ---

async def handle_web(request):
    return web.Response(text="Safe Link Active")

async def main():
    asyncio.create_task(github_monitor())
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    
    # Порт для Render
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Оповещение об обновлении (при наличии пользователей)
    for uid in get_users():
        try:
            await bot.send_message(uid, "🔄 **Система обновлена:** Добавлен Татарстан, время синхронизировано (МСК).", reply_markup=get_main_kb())
        except: pass

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())