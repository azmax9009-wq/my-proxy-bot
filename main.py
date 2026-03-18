import asyncio
import aiohttp
import hashlib
import os
import re
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361 

# СПИСОК ID ПОЛЬЗОВАТЕЛЕЙ ДЛЯ АВТО-УВЕДОМЛЕНИЙ
TARGET_USERS = [
    1201378326, 
    1180353475, 
    6723386873, 
    5209666874, 
    8208699361
] 

PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = ""
last_update_time = "Ожидание..."

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
    await message.answer(
        "👋 **Добро пожаловать в Happ VPN!**\n\n"
        "Вы находитесь в списке приоритетных пользователей. Все обновления будут приходить вам автоматически.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    content = await r.text()
                    total = len(re.findall(r'vless://', content))
                    await bot.send_document(
                        message.chat.id, 
                        BufferedInputFile(content.encode(), filename="Happ_Config.txt"), 
                        caption=f"✅ **Конфигурация Happ готова!**\n🌍 Доступно узлов: **{total}**\n🕒 Обновлено: {last_update_time}",
                        parse_mode="Markdown"
                    )
        except:
            await message.answer("❌ Ошибка связи с сервером GitHub.")

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **ИНСТРУКЦИЯ HAPP**\n\n"
        "1️⃣ Нажмите кнопку **'ПОЛУЧИТЬ НАСТРОЙКИ'** и скачайте файл.\n"
        "2️⃣ Скопируйте весь текст из этого файла.\n"
        "3️⃣ В приложении **Happ** нажмите кнопку **'+' (Add)**.\n"
        "4️⃣ Выберите пункт **'Add from Clipboard'**.\n"
        "5️⃣ Нажмите на иконку щита или кнопку в центре для подключения. ✅"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=com.happ.android")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/happ-proxy/id6477543881")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await message.answer(f"🟢 **Happ VPN Online**\n🕒 Последнее обновление базы: `{last_update_time}`", parse_mode="Markdown")

# --- АДМИНКА ---
@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="adm_br")]
    ])
    await message.answer("👑 **Панель администратора**", reply_markup=kb)

@dp.callback_query(F.data == "adm_br")
async def admin_callback(cb: CallbackQuery):
    await cb.message.answer("Введите команду:\n`/broadcast Текст сообщения`", parse_mode="Markdown")
    await cb.answer()

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast", "").strip()
    if not text: return
    for uid in TARGET_USERS:
        try:
            await bot.send_message(uid, f"📢 **ВАЖНОЕ СООБЩЕНИЕ:**\n\n{text}")
            await asyncio.sleep(0.05)
        except: pass

# --- ПРОВЕРКА GITHUB ---
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
                            if last_hash != "": 
                                for uid in TARGET_USERS:
                                    try: 
                                        await bot.send_message(
                                            uid, 
                                            f"🔔 **ОБНОВЛЕНИЕ ПРОКСИ!**\n\n"
                                            f"На GitHub добавлены новые серверы.\n"
                                            f"Нажмите кнопку получения настроек, чтобы обновить подключение."
                                        )
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

# --- ЗАПУСК ---
async def handle(request): return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # МАССОВАЯ РАССЫЛКА ПРИ КАЖДОМ ОБНОВЛЕНИИ КОДА
    now = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
    for uid in TARGET_USERS:
        try:
            await bot.send_message(
                uid, 
                f"🚀 **Бот Happ VPN успешно обновлен!**\n\n"
                f"🕒 Время запуска: {now} (МСК)\n"
                f"Все функции работают. Новые прокси будут приходить сюда автоматически.",
                reply_markup=get_kb(),
                parse_mode="Markdown"
            )
            await asyncio.sleep(0.05)
        except: pass

    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
