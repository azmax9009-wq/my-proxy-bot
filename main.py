import asyncio, aiohttp, hashlib, os, time, pytz
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

# Ссылки на крутые картинки (Киберпанк/Безопасность)
START_PIC = "https://w.forfun.com/fetch/1f/1f81d113426e2a149a4a755d506927d1.jpeg"
ADMIN_PIC = "https://img.goodfon.ru/original/1920x1080/7/da/mariya-s-shlemom-art-kiberpank-pogranichnik-cyberpunk.jpg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
session = None

# Глобальные переменные для статуса
github_status = "🟢 OK"
last_check_time = "Только что"

# --- СЕРВИСНЫЕ ФУНКЦИИ ---

def save_user(user_id):
    if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w').close()
    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

async def admin_notify(text):
    try:
        await bot.send_message(ADMIN_ID, f"🛠 **LOG:** {text}", parse_mode="MarkdownV2")
    except: pass

def clean_for_iphone(text):
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    return "\n".join([l.strip() for l in text.splitlines() if l.strip().startswith(valid)])

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📸 QR-Код узла"), KeyboardButton(text="📊 Статус Системы")],
        [KeyboardButton(text="🛡 Помощь")]
    ], resize_keyboard=True)

def get_file_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (Happ/Clean)", callback_data="get_iphone")],
        [InlineKeyboardButton(text="🤖 Android / PC (Full)", callback_data="get_android")]
    ])

# --- ОБРАБОТЧИКИ ЮЗЕРОВ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    # Отправляем фото с приветствием
    await bot.send_photo(
        message.chat.id,
        START_PIC,
        caption=(
            "🔥 **Добро пожаловать в CyberSafe VPN**\n\n"
            "Я — твой автоматический оператор узлов безопасности.\n"
            "Для начала работы выбери действие в меню:"
        ),
        reply_markup=get_main_kb(),
        parse_mode="Markdown"
    )
    await admin_notify(f"Зашел: @{message.from_user.username or 'anon'} (`{message.from_user.id}`)")

@dp.message(F.text == "📱 Получить Конфиг")
async def config_menu(message: types.Message):
    await message.answer("🛠 **Выбери платформу:**", reply_markup=get_file_kb())

@dp.callback_query(F.data == "get_iphone")
async def send_iphone(callback: types.CallbackQuery):
    async with session.get(PROXY_URL) as r:
        if r.status == 200:
            clean_data = clean_for_iphone(await r.text())
            await bot.send_document(
                callback.message.chat.id,
                BufferedInputFile(clean_data.encode(), filename="iPhone_Fix.txt"),
                caption="🍏 **Файл очищен для iPhone.**"
            )
            await admin_notify(f"ID {callback.from_user.id} скачал iPhone Fix")
    await callback.answer()

@dp.callback_query(F.data == "get_android")
async def send_android(callback: types.CallbackQuery):
    async with session.get(PROXY_URL) as r:
        if r.status == 200:
            await bot.send_document(
                callback.message.chat.id,
                BufferedInputFile(await r.read(), filename="Standard.txt"),
                caption="📄 **Обычный конфиг (Android/PC)**"
            )
            await admin_notify(f"ID {callback.from_user.id} скачал Полный файл")
    await callback.answer()

@dp.message(F.text == "📸 QR-Код узла")
async def send_qr(message: types.Message):
    async with session.get(PROXY_URL) as r:
        if r.status == 200:
            links = clean_for_iphone(await r.text()).splitlines()
            if links:
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={links[0]}"
                await bot.send_photo(message.chat.id, qr_url, caption="📸 **Быстрый вход (Узел #1)**\nОтсканируй в приложении Happ.")
            else: await message.answer("Links not found.")

@dp.message(F.text == "📊 Статус Системы")
async def status_check(message: types.Message):
    # Пинг до гугла
    start = time.time()
    async with session.get("https://google.com") as r:
        ping = round((time.time() - start) * 1000)
    
    status_text = (
        f"🖥 **Сервис:** `Elite Visual v5.0`\n"
        f"📡 **Пинг:** `{ping} ms`\n"
        f"📅 **Дата:** `{datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m %H:%M')}`\n"
        f"🔷 **GitHub:** `{github_status}` (`{last_check_time}`)"
    )
    await message.answer(status_text, parse_mode="MarkdownV2")

# --- АДМИН-МЯСО И ВИЗУАЛ ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        with open(USERS_FILE, "r") as f:
            count = len(f.read().splitlines())
        # Отправляем фото с Админ-панелью
        await bot.send_photo(
            message.chat.id,
            ADMIN_PIC,
            caption=(
                f"👑 **ЦЕНТР УПРАВЛЕНИЯ**\n\n"
                f"Юзеров: `{count}`\n"
                f"Рассылка: `/send [ТЕКСТ]`\n"
                f"Пинг бота: `/ping`"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📥 База ID", callback_data="db")]]),
            parse_mode="Markdown"
        )

@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    """Скрытый быстрый пинг бота для админа"""
    if message.from_user.id == ADMIN_ID:
        await message.answer("🏓 **Pong!** Bot is alive.")

@dp.message(Command("send"))
async def broadcast(message: types.Message, command: CommandObject):
    if message.from_user.id == ADMIN_ID and command.args:
        with open(USERS_FILE, "r") as f: ids = f.read().splitlines()
        sent = 0
        for uid in ids:
            try:
                await bot.send_message(uid, f"📢 **ВНИМАНИЕ:**\n\n{command.args}")
                sent += 1
                await asyncio.sleep(0.05)
            except: pass
        await message.answer(f"✅ Готово! Доставлено: {sent}")

@dp.callback_query(F.data == "db")
async def send_db(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        await bot.send_document(ADMIN_ID, BufferedInputFile.from_file(USERS_FILE))
    await callback.answer()

# --- СТАНДАРТ ---
@dp.message(F.text == "🛡 Помощь")
async def help_cmd(message: types.Message):
    await message.answer("1. Скачай файл.\n2. Скопируй ссылки.\n3. Добавь в Happ VPN.")

# --- ФОНОВЫЕ ЗАДАЧИ ---

async def monitor_github():
    global github_status, last_check_time
    while True:
        try:
            async with session.get(PROXY_URL) as r:
                last_check_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
                if r.status != 200:
                    github_status = f"🔴 Error {r.status}"
                    await admin_notify(f"⚠️ **GitHub ругается!** Ошибка {r.status}")
                else:
                    github_status = "🟢 Online"
        except:
            github_status = "🔴 ALARM"
            await admin_notify("🚨 **Нет связи с GitHub!**")
        await asyncio.sleep(600)

async def handle_web(request): return web.Response(text="Bot visual v5.0 is running")

async def main():
    global session
    session = aiohttp.ClientSession()
    app = web.Application(); app.router.add_get("/", handle_web)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(monitor_github())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
