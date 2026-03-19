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
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = ""
last_update_time = "Ожидание..."

# --- КЛАВИАТУРЫ ---
def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг"), KeyboardButton(text="⚡ Скорость")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="🆘 Поддержка")]
    ], resize_keyboard=True)

def get_config_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать текст (ВСЕ)", callback_data="copy_text")],
        [InlineKeyboardButton(text="📁 Скачать файл", callback_data="download_file")],
        [InlineKeyboardButton(text="📱 QR-код (первый узел)", callback_data="get_qr")]
    ])

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 **Happ VPN готов к работе!**", reply_markup=get_main_kb(), parse_mode="Markdown")

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def show_options(message: types.Message):
    await message.answer("Выберите формат получения:", reply_markup=get_config_choice_kb())

@dp.callback_query(F.data == "copy_text")
async def handle_copy_text(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=10) as r:
                if r.status == 200:
                    content = await r.text()
                    
                    # Если текст пустой
                    if not content.strip():
                        await callback.answer("База пуста", show_alert=True)
                        return

                    # РАЗБИВКА НА ЧАСТИ (лимит 3800 для запаса)
                    limit = 3800
                    parts = [content[i:i+limit] for i in range(0, len(content), limit)]
                    
                    await callback.message.answer("👇 **Нажимайте на блоки ниже, чтобы скопировать их:**")
                    
                    for part in parts:
                        # Каждую часть шлем отдельным копируемым сообщением
                        await callback.message.answer(f"`{part}`", parse_mode="MarkdownV2")
                        await asyncio.sleep(0.1) # Защита от спам-фильтра TG
                else:
                    await callback.answer("Ошибка GitHub", show_alert=True)
        except Exception as e:
            await callback.answer(f"Ошибка: {str(e)}", show_alert=True)
    
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(F.data == "download_file")
async def handle_download_file(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    content = await r.text()
                    await bot.send_document(
                        callback.message.chat.id,
                        BufferedInputFile(content.encode(), filename="Happ_Config.txt"),
                        caption=f"✅ Конфигурация файлом\n🕒 Обновлено: {last_update_time}"
                    )
        except: pass
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(F.data == "get_qr")
async def handle_qr(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    content = await r.text()
                    first = content.split('\n')[0].strip()
                    if "vless://" in first:
                        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={first}"
                        await callback.message.answer_photo(qr_url, caption="📸 QR-код первого узла")
        except: pass
    await callback.message.delete()
    await callback.answer()

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://google.com", timeout=3):
                ms = round((time.time() - start) * 1000)
                res = f"🟢 Стабильно ({ms} ms)"
        except: res = "🔴 Проблемы"
    await message.answer(f"🌐 **Статус:** {res}\n🕒 **Обновлено:** {last_update_time}", parse_mode="Markdown")

@dp.message(F.text == "📖 Инструкция")
async def inst(m: types.Message):
    await m.answer("1. Нажми 'Скопировать'\n2. Нажми на текст (он скопируется)\n3. Вставь в Happ через '+'", parse_mode="Markdown")

@dp.message(F.text == "🆘 Поддержка")
async def supp(m: types.Message):
    await m.answer(f"Админ: [Связаться](tg://user?id={ADMIN_ID})", parse_mode="MarkdownV2")

# --- ЦИКЛ ПРОВЕРКИ ---
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
                            last_update_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M:%S")
                            if last_hash != "":
                                for uid in TARGET_USERS:
                                    try: await bot.send_message(uid, "🔔 База прокси обновлена!")
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
