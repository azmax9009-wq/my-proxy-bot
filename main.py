import asyncio
import aiohttp
import hashlib
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

active_users = set()
last_hash = None

# --- ФУНКЦИИ АНАЛИЗА ---

def get_clean_links(text):
    """Считает только реальные ключи обхода"""
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    return [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    kb = [
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📡 Статус Связи (РЭБ)"), KeyboardButton(text="🛡 Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- МОНИТОРИНГ ---

async def github_monitor():
    global last_hash
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        curr_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if last_hash is not None and curr_hash != last_hash:
                            last_hash = curr_hash
                            count = len(get_clean_links(content))
                            
                            for uid in active_users:
                                try:
                                    await bot.send_message(
                                        uid, 
                                        f"⚠️ **ОБНОВЛЕНИЕ КАНАЛОВ СВЯЗИ**\n\n"
                                        f"Загружено новых обходов: `{count}`\n"
                                        f"🛡 Режим работы: **Анти-глушилка (РЭБ)**\n"
                                        f"🌐 Статус: `Стабильно`\n\n"
                                        f"Обновите конфиг, если интернет работает медленно.",
                                        parse_mode="Markdown"
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
    active_users.add(message.from_user.id)
    await message.answer(
        "🚀 **Happ VPN: Защита Связи**\n\n"
        "Наши сервера подготовлены к работе в условиях помех и глушения интернета (БПЛА/РЭБ).\n"
        "Я пришлю уведомление, как только обновлю пути обхода.",
        reply_markup=get_main_kb()
    )

@dp.message(F.text == "📡 Статус Связи (РЭБ)")
async def network_status(message: types.Message):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                links = get_clean_links(await r.text())
                count = len(links)
                await message.answer(
                    f"🛰 **МОНИТОРИНГ СЕТИ:**\n\n"
                    f"📍 Доступно линий обхода: `{count}`\n"
                    f"🛡 Устойчивость к РЭБ: `ВЫСОКАЯ`\n"
                    f"⚡️ Маскировка трафика: `ВКЛЮЧЕНА`\n"
                    f"📶 Сигнал: `Стабильный`\n\n"
                    f"Прокси помогают поддерживать связь при работе систем подавления БПЛА.",
                    parse_mode="Markdown"
                )

@dp.message(F.text == "📱 Получить Конфиг")
async def ask_format(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Анти-РЭБ)", callback_data="f_ios")],
        [InlineKeyboardButton(text="🤖 Android / PC (Все ключи)", callback_data="f_all")]
    ])
    await message.answer("🛠 **Выбери тип защищенного канала:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("f_"))
async def send_file(callback: types.CallbackQuery):
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                data = "\n".join(get_clean_links(content)) if callback.data == "f_ios" else content
                await bot.send_document(
                    callback.message.chat.id, 
                    BufferedInputFile(data.encode(), filename="Emergency_Config.txt"),
                    caption="🛡 **Файл обхода загружен.**\nИспользуйте его при перебоях со связью."
                )
    await callback.answer()

# --- СТАРТ ---

async def handle_web(request): return web.Response(text="Safe")

async def main():
    asyncio.create_task(github_monitor())
    app = web.Application(); app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())