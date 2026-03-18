import asyncio
import aiohttp
import hashlib
import os
import time
import re
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
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- ФУНКЦИИ ПРОВЕРКИ ---
async def check_host(host, port):
    try:
        conn = asyncio.open_connection(host, int(port))
        reader, writer = await asyncio.wait_for(conn, timeout=1.5)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

async def get_filtered_config(config_text):
    lines = config_text.strip().split('\n')
    valid_lines = []
    tasks = []
    for line in lines:
        match = re.search(r'@([\w\.-]+):(\d+)', line)
        if match:
            tasks.append((line, check_host(match.group(1), match.group(2))))
    
    results = await asyncio.gather(*(t[1] for t in tasks))
    for i, is_alive in enumerate(results):
        if is_alive:
            valid_lines.append(tasks[i][0])
    return "\n".join(valid_lines), len(lines), len(valid_lines)

# --- КЛАВИАТУРА ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚀 ПОЛУЧИТЬ НАСТРОЙКИ")],
        [KeyboardButton(text="📊 Статус и Пинг"), KeyboardButton(text="⚡ Скорость")],
        [KeyboardButton(text="📖 Инструкция")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "👋 **Добро пожаловать!**\n\nНажмите кнопку ниже, чтобы получить актуальные настройки VPN.",
        reply_markup=get_main_keyboard(), parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    
    hosts = re.findall(r'@([\w\.-]+):(\d+)', content)
    tasks = [check_host(h, p) for h, p in hosts[:15]]
    results = await asyncio.gather(*tasks)
    active = results.count(True)
    
    await message.answer(
        f"🖥 **СТАТУС СИСТЕМЫ**\n\n"
        f"👥 Пользователей: **{len(get_all_users())}**\n"
        f"📡 Активных узлов: `{active}/{len(hosts)}`\n"
        f"🕒 Обновлено: `{last_update_time}`", 
        parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    status_msg = await message.answer("🔍 *Фильтруем рабочие серверы...*")
    await bot.send_chat_action(message.chat.id, "upload_document")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                raw_content = await r.text()
                filtered_content, total, alive = await get_filtered_config(raw_content)
                
                caption = (
                    f"✅ **Файл готов!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🟢 Доступно серверов: **{alive}**\n"
                    f"🕒 Актуально на: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━"
                )
                await status_msg.delete()
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(filtered_content.encode(), filename="proxies.txt"), 
                    caption=caption, 
                    parse_mode="Markdown"
                )

@dp.message(F.text == "⚡ Скорость")
async def speed_test(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="
