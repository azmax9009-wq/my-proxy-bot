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
# Токен твоего бота
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
# Твой ID (админ)
ADMIN_ID = 8208699361
# Список тех, кому придет уведомление об обновлении базы
TARGET_USERS = [1201378326, 1180353475, 6723386873, 5209666874, 8208699361]
# Ссылка на твой конфиг на GitHub (RAW версия)
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Глобальные переменные для отслеживания изменений
last_hash = ""
last_update_time = "Ожидание обновления..."
session = None

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def escape_md(text):
    """Экранирование символов для MarkdownV2"""
    return re.sub(r'([\_\*\[\]\(\)\~\`\\\>\#\+\-\=\|\{\}\.\!])', r'\\\1', text)

def get_clean_content(raw_text):
    """
    ГЛАВНАЯ ФУНКЦИЯ: 
    Удаляет все строки, которые начинаются на # (те самые абзацы).
    Оставляет только прямые ссылки на прокси.
    """
    # Список разрешенных протоколов
    valid_protocols = ('vless://', 'trojan://', 'ss://', 'vmess://', 'hysteria2://', 'tuic://')
    lines = raw_text.splitlines()
    
    # Оставляем только строки, которые начинаются с протокола (игнорируем # и пустые строки)
    clean_lines = [line.strip() for line in lines if line.strip().startswith(valid_protocols)]
    
    return "\n".join(clean_lines)

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг"), KeyboardButton(text="⚡ Скорость")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="🆘 Поддержка")]
    ], resize_keyboard=True)

def get_config_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать (Чистые ссылки)", callback_data="copy_text_hidden")],
        [InlineKeyboardButton(text="📁 Скачать файл (.txt)", callback_data="download_file")],
        [InlineKeyboardButton(text="📱 QR-код (первый узел)", callback_data="get_qr")]
    ])

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Добро пожаловать в Happ VPN!**\n\n"
        "Я автоматически очищаю конфиги от лишнего текста, "
        "чтобы они корректно работали на iPhone и Android.",
        reply_markup=get_main_kb(), 
        parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def show_options(message: types.Message):
    await message.answer("Выберите удобный формат получения:", reply_markup=get_config_choice_kb())

@dp.callback_query(F.data == "copy_text_hidden")
async def handle_copy_hidden(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                raw_text = await r.text()
                # Чистим текст от комментариев (#)
                content = get_clean_content(raw_text)

                if not content:
                    await callback.answer("❌ На GitHub нет рабочих ссылок", show_alert=True)
                    return

                await callback.message.answer("🎯 *Нажми на текст ниже, чтобы скопировать:*", parse_mode="Markdown")
                
                # Telegram не дает отправлять больше 4096 символов в одном сообщении
                limit = 3500
                parts = [content[i:i+limit] for i in range(0, len(content), limit)]
                for part in parts:
                    await callback.message.answer(f"||`{escape_md(part)}`||", parse_mode="MarkdownV2")
                    await asyncio.sleep(0.3)
            else:
                await callback.answer("❌ Ошибка загрузки с GitHub", show_alert=True)
    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)[:40]}", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "download_file")
async def handle_download_file(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                content = get_clean_content(await r.text())
                file_data = content.encode('utf-8')
                await bot.send_document(
                    callback.message.chat.id,
                    BufferedInputFile(file_data, filename="Happ_Configs.txt"),
                    caption=f"✅ **Чистый список конфигов**\n🕒 Обновлено: {last_update_time}",
                    parse_mode="Markdown"
                )
    except:
        await callback.answer("Ошибка при создании файла", show_alert=True)
    await callback.answer()

@dp.callback_query(F.data == "get_qr")
async def handle_qr(callback: CallbackQuery):
    global session
    try:
        async with session.get(PROXY_URL, timeout=10) as r:
            if r.status == 200:
                content = get_clean_content(await r.text())
                configs = content.splitlines()
                if configs:
                    # Создаем QR для первого рабочего узла
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={configs[0]}"
                    await callback.message.answer_photo(qr_url, caption="📸 **Первый узел из списка**\nОтсканируй камерой или в приложении.")
                else:
                    await callback.answer("Ссылок не найдено", show_alert=True)
    except:
        await callback.answer("Ошибка генерации QR", show_alert=True)
    await callback.answer()

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    start_time = time.time()
    try:
        async with session.get("https://google.com", timeout=3) as r:
            ping = round((time.time() - start_time) * 1000)
            res = f"🟢 Сеть в норме ({ping} ms)"
    except:
        res = "🔴 Проблемы с соединением"
    await message.answer(f"🛰 **Статус бота:** {res}\n🕒 **Последнее обновление базы:** `{last_update_time}`", parse_mode="Markdown")

@dp.message(F.text == "🆘 Поддержка")
async def support_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👨‍💻 Написать админу", url=f"tg://user?id={ADMIN_ID}")]])
    await message.answer("Если что-то не работает — пиши админу напрямую.", reply_markup=kb)

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    await message.answer(
        "📖 **КАК ПОЛЬЗОВАТЬСЯ:**\n"
        "1. Нажми 'Получить настройки'.\n"
        "2. Скопируй текст (нажми на него).\n"
        "3. Открой приложение **Happ** (или Shadowrocket/V2Ray).\n"
        "4. Нажми значок **[+]** и выбери **'Add from Clipboard'** (Добавить из буфера).", 
        parse_mode="Markdown"
    )

# --- ФОНОВЫЕ ЗАДАЧИ ---

async def check_github_loop():
    """Проверка обновлений на GitHub раз в минуту"""
    global last_hash, last_update_time, session
    while True:
        try:
            async with session.get(PROXY_URL, timeout=15) as r:
                if r.status == 200:
                    content = await r.text()
                    new_hash = hashlib.md5(content.encode()).hexdigest()
                    
                    if new_hash != last_hash:
                        now = datetime.now(pytz.timezone('Europe/Moscow'))
                        last_update_time = now.strftime("%d.%m %H:%M")
                        
                        # Если это не первый запуск — уведомляем пользователей
                        if last_hash != "":
                            for uid in TARGET_USERS:
                                try:
                                    await bot.send_message(uid, "🔔 **База VPN обновлена!**\nЗайдите в бота и обновите настройки.")
                                except:
                                    pass
                        last_hash = new_hash
        except:
            pass
        await asyncio.sleep(60)

# --- WEB СЕРВЕР ДЛЯ RENDER ---

async def handle_web(request):
    return web.Response(text="Bot is online")

async def main():
    global session
    session = aiohttp.ClientSession()
    
    # Запуск веб-сервера (чтобы Render не отключал бота)
    app = web.Application()
    app.router.add_get('/', handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
