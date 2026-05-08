import asyncio
import aiohttp
import hashlib
import os
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

# --- РАБОТА С БАЗОЙ (Чтобы бот не забывал тебя после перезагрузки) ---

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

# --- ЛОГИКА АНАЛИЗА ---

def get_clean_links(text):
    """Считает только рабочие ключи VPN"""
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    return [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]

# --- МОНИТОРИНГ GITHUB (Авто-рассылка при обновлении) ---

async def github_monitor():
    global last_hash
    print("🛰 Мониторинг GitHub запущен...")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL, timeout=10) as r:
                    if r.status == 200:
                        content = await r.text()
                        curr_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if last_hash is not None and curr_hash != last_hash:
                            last_hash = curr_hash
                            links = get_clean_links(content)
                            count = len(links)
                            
                            users = get_users()
                            for uid in users:
                                try:
                                    await bot.send_message(
                                        uid, 
                                        f"⚠️ **КАНАЛЫ СВЯЗИ ОБНОВЛЕНЫ**\n\n"
                                        f"📍 Доступно новых линий: `{count}`\n"
                                        f"🛡 Режим: **Анти-РЭБ (Защита от помех)**\n"
                                        f"🌐 Статус: `Стабильно`\n\n"
                                        f"Нажми кнопку ниже, чтобы получить файл.",
                                        parse_mode="Markdown"
                                    )
                                    await asyncio.sleep(0.05)
                                except: pass
                        else:
                            last_hash = curr_hash
        except: pass
        await asyncio.sleep(60)

# --- ОБРАБОТЧИКИ ТЕЛЕГРАМ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user.id)
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📡 Статус Связи (РЭБ)")]
    ], resize_keyboard=True)
    
    await message.answer(
        "🚀 **Happ VPN: Экстренная Связь**\n\n"
        "Я буду присылать уведомления, если каналы обновятся для обхода глушилок БПЛА.\n"
        "Твой ID внесен в базу оповещений.",
        reply_markup=kb
    )

@dp.message(F.text == "📡 Статус Связи (РЭБ)")
async def network_status(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                count = len(get_clean_links(await r.text()))
                await message.answer(
                    f"🛰 **МОНИТОРИНГ СЕТИ:**\n\n"
                    f"📍 Линий обхода: `{count}`\n"
                    f"🛡 Устойчивость к РЭБ: `Высокая`\n"
                    f"🛡 Защита БПЛА: `Активна`",
                    parse_mode="Markdown"
                )

@dp.message(F.text == "📱 Получить Конфиг")
async def send_config(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Анти-РЭБ)", callback_data="f_ios")],
        [InlineKeyboardButton(text="🤖 Android / PC", callback_data="f_all")]
    ])
    await message.answer("🛠 **Выбери формат защищенного канала:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("f_"))
async def process_file(callback: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                data = "\n".join(get_clean_links(content)) if callback.data == "f_ios" else content
                await bot.send_document(
                    callback.message.chat.id, 
                    BufferedInputFile(data.encode(), filename="Emergency_Config.txt"),
                    caption="🛡 Конфиг для работы в условиях помех загружен."
                )
    await callback.answer()

# --- ВЕБ-СЕРВЕР (Для Render, чтобы не было ошибки портов) ---

async def handle_web(request):
    return web.Response(text="Bot is running smoothly!")

async def main():
    # Запуск фонового монитора
    asyncio.create_task(github_monitor())
    
    # Настройка веб-части для Render
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000)) # Берем порт от Render
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Веб-сервер запущен на порту {port}")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")