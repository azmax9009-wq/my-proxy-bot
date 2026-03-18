import asyncio
import aiohttp
import hashlib
import os
import random
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- ПОЛЕЗНЫЕ СОВЕТЫ ---
TIPS = [
    "💡 Совет: Если VPN не подключается, попробуйте перезагрузить авиарежим.",
    "💡 Совет: Приложение Hiddify лучше всего работает на последней версии Android/iOS.",
    "💡 Совет: Если скорость упала, проверьте, не включены ли другие VPN-сервисы.",
    "💡 Совет: Файл настроек обновляется автоматически, следите за уведомлениями!",
    "💡 Совет: Если кнопка в Hiddify долго крутится, попробуйте нажать её еще раз."
]

# --- ФУНКЦИИ СПИСКА ---
def save_user(user_id):
    user_id_str = str(user_id)
    try:
        users = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as fr: users = fr.read().splitlines()
        if user_id_str not in users:
            with open(USERS_FILE, "a") as f: f.write(user_id_str + "\n")
            return True
    except: pass
    return False

def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    try:
        with open(USERS_FILE, "r") as f: 
            return [int(l.strip()) for l in f if l.strip().isdigit()]
    except: return [USER_ID]

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="📊 Статус системы"), KeyboardButton(text="⚡ Скорость")]
    ], resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=15) as resp:
                if resp.status == 200: return (await resp.text()).strip()
        except: pass
    return None

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать в сервис!**\n\n"
        "Я помогу вам настроить свободный доступ в интернет.\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Нажмите кнопку ниже, чтобы начать.",
        reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id != USER_ID: return 
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2: return await message.answer("❌ Формат: `/broadcast Текст`")
    text = parts[1]
    users = get_all_users()
    sent = 0
    status = await message.answer(f"⏳ Рассылаю на {len(users)} чел...")
    for uid in users:
        try:
            await bot.send_message(uid, f"📢 **СООБЩЕНИЕ:**\n\n{text}", parse_mode="Markdown")
            sent += 1
            await asyncio.sleep(0.05)
        except: continue
    await status.edit_text(f"✅ Готово! Доставлено: {sent} чел.")

@dp.message(Command("count"))
async def count_users(message: types.Message):
    if message.from_user.id != USER_ID: return
    count = len(get_all_users())
    await message.answer(f"👥 Всего пользователей в базе: **{count}**", parse_mode="Markdown")

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    help_text = (
        "📖 **ИНСТРУКЦИЯ ПО НАСТРОЙКЕ**\n\n"
        "1. Установите **Hiddify** по ссылкам ниже.\n"
        "2. Нажмите **«🚀 ПОЛУЧИТЬ НАСТРОЙКИ»** в этом боте.\n"
        "3. Скопируйте текст из присланного файла.\n"
        "4. В приложении Hiddify нажмите значок `+` (или `Новый профиль`).\n"
        "5. Выберите пункт **«Из буфера»**.\n"
        "6. Нажмите большую кнопку в центре экрана.\n\n"
        f"_{random.choice(TIPS)}_"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Скачать для Android", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="🍎 Скачать для iPhone", url="https://apps.apple.com/us/app/hiddify-next/id6473777529")]
    ])
    await message.answer(help_text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "⚡ Скорость")
async def check_speed(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Проверить скорость (Fast.com)", url="https://fast.com/ru/")]
    ])
    await message.answer("📏 Нажмите для проверки скорости после подключения:", reply_markup=kb)

@dp.message(F.text == "📊 Статус системы")
async def about_bot(message: types.Message):
    status_text = (
        f"🖥 **СТАТУС СЕРВЕРА**\n\n"
        f"✅ Бот работает стабильно\n"
        f"📅 Обновлено: `{last_update_time}` МСК\n\n"
        f"_{random.choice(TIPS)}_"
    )
    await message.answer(status_text, parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def get_file(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "upload_document") # Показывает "отправка файла"
    proxies = await get_proxies()
    if proxies:
        file_data = proxies.encode('utf-8')
        caption = (
            f"✅ **Ваш файл настроек готов!**\n\n"
            f"Скопируйте всё содержимое и вставьте в Hiddify.\n"
            f"🕒 Актуально на: {last_update_time}"
        )
        await bot.send_document(
            message.chat.id, 
            BufferedInputFile(file_data, filename="proxies.txt"), 
            caption=caption,
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Ошибка связи с GitHub. Попробуйте снова.")

# --- МОНИТОРИНГ ---
async def check_proxies_loop():
    global last_hash, last_update_time
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                if last_hash != "start_node":
                    msg = "🔔 **ОБНОВЛЕНИЕ КОНФИГУРАЦИИ!**\n\nПоявились новые настройки. Заберите их кнопкой «🚀 ПОЛУЧИТЬ НАСТРОЙКИ»."
                    for uid in get_all_users():
                        try: await bot.send_message(uid, msg, parse_mode="Markdown"); await asyncio.sleep(0.1)
                        except: pass
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def handle(request): return web.Response(text="Bot is running")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
