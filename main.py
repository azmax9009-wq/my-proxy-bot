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
from aiogram.types import (
    BufferedInputFile, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361
TARGET_USERS = [1201378326, 1180353475, 6723386873, 5209666874, 8208699361]

# Ссылка должна вести на RAW файл
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = ""
last_update_time = "Ожидание..."
session = None # Глобальная сессия

def escape_md(text):
    """Экранирование спецсимволов для MarkdownV2"""
    return re.sub(r'([\_\*\[\]\(\)\~\`\\\>\#\+\-\=\|\{\}\.\!])', r'\\\1', text)

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг"), KeyboardButton(text="⚡ Скорость")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="🆘 Поддержка")]
    ], resize_keyboard=True)

def get_config_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ВСЁ (Скрыто)", callback_data="copy_text_hidden")],
        [InlineKeyboardButton(text="📁 Скачать файл (.txt)", callback_data="download_file")],
        [InlineKeyboardButton(text="📱 QR-код (первый узел)", callback_data="get_qr")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в Happ VPN!**\n\n"
        "Я помогу вам получить актуальные настройки. Используйте меню ниже.",
        reply_markup=get_main_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def show_options(message: types.Message):
    await message.answer(
        "Выберите формат получения конфигурации:",
        reply_markup=get_config_choice_kb()
    )

@dp.callback_query(F.data == "copy_text_hidden")
async def handle_copy_hidden(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                content = await r.text()
                if not content.strip():
                    await callback.answer("❌ База пуста!", show_alert=True)
                    return

                await callback.message.answer("🎯 *Нажмите на блок ниже, он скопируется автоматически:*", parse_mode="Markdown")
                
                # Лимит Telegram 4096 символов. Берем 3500 для безопасности.
                limit = 3500
                parts = [content[i:i+limit] for i in range(0, len(content), limit)]
        
                for part in parts:
                    safe_part = escape_md(part)
                    # Конструкция ||`text`|| делает текст скрытым (спойлер) и копируемым (моноширинным)
                    hidden_msg = f"||`{safe_part}`||"
                    await callback.message.answer(hidden_msg, parse_mode="MarkdownV2")
                    await asyncio.sleep(0.3) 
            else:
                await callback.answer(f"❌ Ошибка GitHub: {r.status}", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}", show_alert=True)
    
    await callback.answer()

@dp.callback_query(F.data == "download_file")
async def handle_download_file(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                content = await r.text()
                await bot.send_document(
                    callback.message.chat.id,
                    BufferedInputFile(content.encode(), filename="Happ_Config.txt"),
                    caption=f"✅ **Файл готов!**\n🕒 Обновлено: {last_update_time}",
                    parse_mode="Markdown"
                )
    except: pass
    await callback.answer()

@dp.callback_query(F.data == "get_qr")
async def handle_qr(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                content = await r.text()
                configs = [line.strip() for line in content.split('\n') if "vless://" in line]
                if configs:
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={configs[0]}"
                    await callback.message.answer_photo(qr_url, caption="📸 **QR-код для импорта первого узла**")
                else:
                    await callback.answer("❌ VLESS ссылки не найдены в файле", show_alert=True)
    except: pass
    await callback.answer()

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    start_time = time.time()
    global session
    try:
        async with session.get("https://google.com", timeout=3) as r:
            ping = round((time.time() - start_time) * 1000)
            res = f"🟢 Стабильно ({ping} ms)"
    except: res = "🔴 Проблемы с сетью"
    await message.answer(f"🛰 **Статус:** {res}\n🕒 **База обновлена:** `{last_update_time}`", parse_mode="Markdown")

@dp.message(F.text == "🆘 Поддержка")
async def support_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Написать админу", url=f"tg://user?id={ADMIN_ID}")]
    ])
    await message.answer("Есть вопросы? Напишите нам:", reply_markup=kb)

# --- ФОНОВАЯ ПРОВЕРКА ОБНОВЛЕНИЙ ---
async def check_github_loop():
    global last_hash, last_update_time, session
    while True:
        try:
            async with session.get(PROXY_URL, timeout=15) as r:
                if r.status == 200:
                    content = await r.text()
                    new_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if new_hash != last_hash:
                        now = datetime.now(pytz.timezone('Europe/Moscow'))
                        last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                        
                        if last_hash != "": # Не спамим при самом первом запуске
                            for uid in TARGET_USERS:
                                try:
                                    await bot.send_message(uid, "🔔 **ОБНОВЛЕНИЕ ПРОКСИ!**\nДобавлены новые серверы. Нажмите 'ПОЛУЧИТЬ НАСТРОЙКИ'.")
                                except: pass
                        last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

# --- ЗАПУСК ---
async def handle_web(request): return web.Response(text="Bot is running")

async def main():
    global session
    session = aiohttp.ClientSession() # Создаем одну сессию на весь период работы
    
    app = web.Application()
    app.router.add_get('/', handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_github_loop())
    
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
