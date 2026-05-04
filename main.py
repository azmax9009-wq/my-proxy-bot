import asyncio, aiohttp, hashlib, os, time, pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ (ПРОВЕРЬ ИХ!) ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'
USERS_FILE = "users_list.txt"

# Картинки для красоты
START_PIC = "https://w.forfun.com/fetch/1f/1f81d113426e2a149a4a755d506927d1.jpeg"
ADMIN_PIC = "https://img.goodfon.ru/original/1920x1080/7/da/mariya-s-shlemom-art-kiberpank-pogranichnik-cyberpunk.jpg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
session = None

# --- ФУНКЦИИ ---

def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: pass
    
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")
        return True
    return False

async def admin_notify(text):
    try:
        await bot.send_message(ADMIN_ID, f"🛠 **LOG:** {text}")
    except: pass

def clean_for_iphone(text):
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]
    return "\n".join(lines)

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    kb = [
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📸 QR-Код"), KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="🛡 Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_file_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (.txt без мусора)", callback_data="f_iphone")],
        [InlineKeyboardButton(text="🤖 Android / PC (Полный .txt)", callback_data="f_android")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_new = save_user(message.from_user.id)
    msg = "🔥 **Happ VPN Online**\n\nВыбери тип конфига в меню ниже:"
    if is_new:
        await admin_notify(f"Новый юзер! @{message.from_user.username or 'anon'}")
    
    try:
        await bot.send_photo(message.chat.id, START_PIC, caption=msg, reply_markup=get_main_kb(), parse_mode="Markdown")
    except:
        await message.answer(msg, reply_markup=get_main_kb(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def config_menu(message: types.Message):
    await message.answer("🛠 **Выбери формат файла:**", reply_markup=get_file_kb())

@dp.callback_query(F.data.startswith("f_"))
async def send_file(callback: types.CallbackQuery):
    await callback.answer("Подключаюсь к серверу...")
    async with session.get(PROXY_URL) as r:
        if r.status == 200:
            content = await r.text()
            if callback.data == "f_iphone":
                final_data = clean_for_iphone(content)
                filename = "iPhone_Configs.txt"
                cap = "🍏 Очищено для iPhone"
            else:
                final_data = content
                filename = "Full_Configs.txt"
                cap = "📄 Полный файл"
            
            await bot.send_document(
                callback.message.chat.id,
                BufferedInputFile(final_data.encode(), filename=filename),
                caption=cap
            )
            await admin_notify(f"Юзер {callback.from_user.id} скачал {filename}")

@dp.message(F.text == "📸 QR-Код")
async def send_qr(message: types.Message):
    async with session.get(PROXY_URL) as r:
        if r.status == 200:
            links = clean_for_iphone(await r.text()).splitlines()
            if links:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={links[0]}"
                await bot.send_photo(message.chat.id, qr_url, caption="📸 **QR для быстрого входа**")
            else:
                await message.answer("Нет ссылок для QR.")

@dp.message(F.text == "📊 Статус")
async def status_check(message: types.Message):
    await message.answer("🛰 Система: `Online`\n📡 GitHub: `Связь стабильна`", parse_mode="Markdown")

# --- АДМИНКА ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = 0
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                count = len(f.read().splitlines())
        
        await bot.send_photo(
            message.chat.id, ADMIN_PIC,
            caption=f"👑 **АДМИН-ПАНЕЛЬ**\n\nЮзеров в базе: `{count}`\nРассылка: `/send текст`",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📥 Скачать базу ID", callback_data="db")]])
        )

@dp.message(Command("send"))
async def broadcast(message: types.Message, command: CommandObject):
    if message.from_user.id == ADMIN_ID and command.args:
        with open(USERS_FILE, "r") as f:
            ids = f.read().splitlines()
        sent = 0
        for uid in ids:
            try:
                await bot.send_message(uid, f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{command.args}")
                sent += 1
                await asyncio.sleep(0.05)
            except: pass
        await message.answer(f"✅ Доставлено: {sent}")

@dp.callback_query(F.data == "db")
async def download_db(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await bot.send_document(ADMIN_ID, BufferedInputFile.from_file(USERS_FILE), caption="База ID")
    await callback.answer()

# --- ЗАПУСК ---

async def handle_web(request): return web.Response(text="Bot is running")

async def main():
    global session
    session = aiohttp.ClientSession()
    app = web.Application(); app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
