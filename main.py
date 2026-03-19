import asyncio
import aiohttp
import hashlib
import os
import re
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from aiohttp import web

# --- НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ОБНОВИТЕ ТОКЕН У @BotFather) ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361

# Список ID пользователей для авто-уведомлений
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

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг")],
        [KeyboardButton(text="⚡ Скорость"), KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

def get_config_inline_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Скопировать текстом", callback_data="get_text_config")],
        [InlineKeyboardButton(text="📁 Скачать файлом", callback_data="get_file_config")]
    ])

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в Happ VPN!**\n\n"
        "Выберите способ получения настроек ниже. Обновления приходят автоматически.",
        reply_markup=get_main_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def config_choice(message: types.Message):
    await message.answer(
        "Как вам удобнее получить конфигурацию?",
        reply_markup=get_config_inline_kb()
    )

@dp.callback_query(F.data == "get_file_config")
async def send_config_file(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    content = await r.text()
                    total = len(re.findall(r'vless://', content))
                    await bot.send_document(
                        callback.message.chat.id, 
                        BufferedInputFile(content.encode(), filename="Happ_Config.txt"), 
                        caption=f"✅ **Файл готов!**\n🌍 Узлов: **{total}**\n🕒 Обновлено: {last_update_time}",
                        parse_mode="Markdown"
                    )
                else:
                    await callback.answer("❌ Ошибка сервера GitHub", show_alert=True)
        except:
            await callback.answer("❌ Ошибка связи", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "get_text_config")
async def send_config_text(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    content = await r.text()
                    # Обрезаем до лимита сообщения Telegram (4096 символов)
                    trimmed_content = content[:3900] 
                    
                    # Используем моноширинный шрифт для функции "Нажми чтобы скопировать"
                    response_text = (
                        "👇 **Нажмите на текст ниже, он скопируется автоматически:**\n\n"
                        f"`{trimmed_content}`"
                    )
                    
                    await callback.message.answer(response_text, parse_mode="MarkdownV2")
                else:
                    await callback.answer("❌ Ошибка сервера GitHub", show_alert=True)
        except:
            await callback.answer("❌ Ошибка связи", show_alert=True)
    await callback.answer()

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **ИНСТРУКЦИЯ HAPP**\n\n"
        "1️⃣ Нажмите **'Скопировать текстом'**.\n"
        "2️⃣ Нажмите на появившийся блок с кодом (он скопируется).\n"
        "3️⃣ В приложении **Happ** нажмите кнопку **'+' (Add)**.\n"
        "4️⃣ Выберите пункт **'Add from Clipboard'**.\n"
        "5️⃣ Подключитесь. ✅"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", url="https://play.google.com/store/apps/details?id=com.happ.android")],
        [InlineKeyboardButton(text="🍎 iPhone", url="https://apps.apple.com/us/app/happ-proxy/id6477543881")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await message.answer(f"🟢 **Happ VPN Online**\n🕒 База обновлена: `{last_update_time}`", parse_mode="Markdown")

# --- ПРОВЕРКА GITHUB (ФОНОВЫЙ ПРОЦЕСС) ---
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
                                            "🔔 **ОБНОВЛЕНИЕ ПРОКСИ!**\n\nДобавлены новые серверы. Нажмите 'ПОЛУЧИТЬ НАСТРОЙКИ' для обновления.",
                                            parse_mode="Markdown"
                                        )
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

# --- ЗАПУСК ---
async def handle(request): return web.Response(text="OK")

async def main():
    # Простейший веб-сервер для поддержки жизни процесса на хостингах
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Уведомление о перезапуске бота
    now = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M")
    for uid in TARGET_USERS:
        try:
            await bot.send_message(uid, f"🚀 **Бот Happ VPN обновлен и запущен!**\n🕒 Время: {now} (МСК)", reply_markup=get_main_kb())
        except: pass

    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
