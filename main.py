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

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# База в памяти
active_users = set()
last_hash = None

# --- ФУНКЦИИ ОЧИСТКИ ---

def get_iphone_version(text):
    """Оставляет только протоколы, которые ест стандартный iOS клиент"""
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]
    return "\n".join(lines)

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    kb = [[KeyboardButton(text="📱 Получить Конфиг")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_format_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Только ссылки)", callback_data="type_ios")],
        [InlineKeyboardButton(text="🤖 Все прокси (Полный файл)", callback_data="type_all")]
    ])

# --- МОНИТОРИНГ ---

async def github_monitor():
    global last_hash
    print("🛰 Мониторинг запущен...")
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        curr_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if last_hash is not None and curr_hash != last_hash:
                            last_hash = curr_hash
                            # При обновлении шлем сразу полную версию всем
                            for uid in active_users:
                                try:
                                    await bot.send_message(uid, "🆕 **Обновление на GitHub!**\nДержи свежий полный список:")
                                    await bot.send_document(uid, BufferedInputFile(content.encode(), filename="Full_Configs.txt"))
                                    await asyncio.sleep(0.05)
                                except: pass
                        else:
                            last_hash = curr_hash
        except: pass
        await asyncio.sleep(30)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    active_users.add(message.from_user.id)
    await message.answer("🚀 **Бот готов!**\nВыбирай формат кнопкой ниже. При обновлении на GitHub я пришлю файл сам.", 
                         reply_markup=get_main_kb())

@dp.message(F.text == "📱 Получить Конфиг")
async def show_formats(message: types.Message):
    await message.answer("🛠 **В каком формате прислать?**", reply_markup=get_format_kb())

@dp.callback_query(F.data.startswith("type_"))
async def send_specific_file(callback: types.CallbackQuery):
    await callback.answer("Подключаюсь к GitHub...")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                if callback.data == "type_ios":
                    final_data = get_iphone_version(content)
                    fname = "iPhone_Only.txt"
                    cap = "🍏 Только подходящие для iOS ссылки"
                else:
                    final_data = content
                    fname = "Full_List.txt"
                    cap = "📄 Полный список прокси"
                
                await bot.send_document(
                    callback.message.chat.id,
                    BufferedInputFile(final_data.encode(), filename=fname),
                    caption=cap
                )

# --- СТАРТ ---

async def handle_web(request): return web.Response(text="OK")

async def main():
    asyncio.create_task(github_monitor())
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())