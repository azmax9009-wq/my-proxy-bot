import asyncio
import aiohttp
import hashlib
import os
import re
import time
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 # Твой ID для админки
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- УТИЛИТЫ ---
def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    try:
        with open(USERS_FILE, "r") as f: 
            return list(set([int(l.strip()) for l in f if l.strip().isdigit()]))
    except: return [USER_ID]

def save_user(user_id):
    u_id = str(user_id)
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if u_id not in users:
        with open(USERS_FILE, "a") as f: f.write(u_id + "\n")

# --- КЛАВИАТУРА ---
def get_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать в VPN-центр Happ!**\n\n"
        "Я помогу вам настроить свободный интернет. Используйте кнопки меню ниже.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **ИНСТРУКЦИЯ ДЛЯ ПРИЛОЖЕНИЯ HAPP**\n\n"
        "**1️⃣ Установите Happ**\n"
        "Скачайте приложение по ссылкам ниже.\n\n"
        "**2️⃣ Получите настройки**\n"
        "Нажмите кнопку **'🚀 ПОЛУЧИТЬ НАСТРОЙКИ'** и скачайте файл.\n\n"
        "**3️⃣ Импорт**\n"
        "• Скопируйте текст из файла.\n"
        "• В приложении **Happ** нажмите **'+' (Add)** -> **'Add from Clipboard'**.\n\n"
        "**4️⃣ Включайте!**"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=com.happ.android")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/happ-proxy/id6477543881")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                total = len(re.findall(r'vless://', content))
                caption = f"✅ **Конфиг для Happ READY!**\n🌍 Узлов: {total}\n🕒 Обновлено: {last_update_time}"
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(content.encode(), filename="Happ_Config.txt"), 
                    caption=caption, parse_mode="Markdown"
                )

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await message.answer(f"🟢 Сервис Happ VPN онлайн\n👥 Пользователей в базе: {len(get_all_users())}\n🕒 Данные: {last_update_time}", parse_mode="Markdown")

@dp.message(F.text == "⚡ Скорость")
async def speed_test(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Тест скорости", url="https://fast.com/ru/")]])
    await message.answer("📏 Проверьте скорость вашего соединения по кнопке ниже:", reply_markup=kb, parse_mode="Markdown")

# --- АДМИН-ПАНЕЛЬ ---
@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != USER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="adm_br"), 
         InlineKeyboardButton(text="📊 Список ID", callback_data="adm_ids")]
    ])
    await message.answer(f"👑 **Админ-центр**\nВсего юзеров: {len(get_all_users())}", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_"))
async def admin_callback(cb: CallbackQuery):
    if cb.from_user.id != USER_ID: return
    if cb.data == "adm_br":
        await cb.message.answer("Чтобы отправить сообщение всем, используй:\n`/broadcast Текст сообщения`", parse_mode="Markdown")
    elif cb.data == "adm_ids":
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "rb") as f:
                await cb.message.answer_document(BufferedInputFile(f.read(), filename="users.txt"))
    await cb.answer()

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != USER_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in get_all_users():
        try: 
            await bot.send_message(uid, f"📢 **ВАЖНОЕ УВЕДОМЛЕНИЕ:**\n\n{text}")
            await asyncio.sleep(0.05)
        except: pass

# --- СИСТЕМНЫЕ ЦИКЛЫ ---
async def check_github_loop():
    global last_hash, last_update_time
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        new_hash = hashlib.md5(content.encode()).hexdigest()
                        if new_hash != last_hash:
                            now = datetime.now(pytz.timezone('Europe/Moscow'))
                            last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                            if last_hash != "start_node":
                                for uid in get_all_users():
                                    try: await bot.send_message(uid, f"🔔 **ОБНОВЛЕНИЕ!** Новые серверы добавлены.\nВремя: {last_update_time}")
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="Happ Bot Active")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Авто-рассылка всем при перезапуске
    all_users = get_all_users()
    now = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
    for uid in all_users:
        try:
            await bot.send_message(
                uid, 
                f"✅ **Бот Happ обновлен и готов!** ({now} МСК)\nВсе системы работают штатно.",
                reply_markup=get_kb(), parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)
        except: pass

    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
