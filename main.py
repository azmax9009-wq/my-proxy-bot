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
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание..."

# --- УТИЛИТЫ ---
def get_all_users():
    if not os.path.exists(USERS_FILE): return [USER_ID]
    with open(USERS_FILE, "r") as f: 
        return [int(l.strip()) for l in f if l.strip().isdigit()]

def save_user(user_id):
    u_id = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write(u_id + "\n")
        return
    with open(USERS_FILE, "r") as f: users = f.read().splitlines()
    if u_id not in users:
        with open(USERS_FILE, "a") as f: f.write(u_id + "\n")

async def check_host(host, port):
    try:
        conn = asyncio.open_connection(host, int(port))
        reader, writer = await asyncio.wait_for(conn, timeout=2.0)
        writer.close()
        await writer.wait_closed()
        return True
    except: return False

# --- КЛАВИАТУРА ГЛАВНОГО МЕНЮ ---
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
        "👋 **Ваш персональный VPN-центр готов!**\n\n"
        "Используйте меню ниже, чтобы скачать настройки или узнать, как ими пользоваться.",
        reply_markup=get_kb(), parse_mode="Markdown"
    )

@dp.message(F.text == "📖 Инструкция")
async def instruction(message: types.Message):
    text = (
        "📖 **КАК ПОДКЛЮЧИТЬ VPN?**\n\n"
        "**Шаг 1: Установите Hiddify**\n"
        "Выберите вашу платформу и установите официальное приложение по кнопкам ниже. 👇\n\n"
        "**Шаг 2: Получите настройки**\n"
        "Нажмите кнопку **'🚀 ПОЛУЧИТЬ НАСТРОЙКИ'** в главном меню и скачайте файл.\n\n"
        "**Шаг 3: Импорт в приложение**\n"
        "• Откройте скачанный файл и **скопируйте весь текст**.\n"
        "• В приложении Hiddify нажмите **'+' (Новый профиль)**.\n"
        "• Выберите **'Из буфера обмена'**.\n\n"
        "**Шаг 4: Поехали!**\n"
        "Нажмите на большую круглую кнопку подключения. Если всё сделано верно — интернет станет свободным! ✅"
    )
    
    # Кнопки для скачивания прямо под инструкцией
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android (Play Store)", url="https://play.google.com/store/apps/details?id=app.hiddify.com")],
        [InlineKeyboardButton(text="🍎 iPhone (App Store)", url="https://apps.apple.com/us/app/hiddify-next/id6473777529")],
        [InlineKeyboardButton(text="💻 Windows (PC)", url="https://github.com/hiddify/hiddify-next/releases/latest/download/Hiddify-Windows-Setup-x64.exe")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.message(F.text == "⚡ Скорость")
async def speed_test(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать Speedtest", url="https://fast.com/ru/")]
    ])
    await message.answer(
        "📏 **Проверка скорости**\n\n"
        "Нажмите на кнопку ниже, чтобы замерить скорость интернета через сервис Fast.com (от Netflix).\n\n"
        "*Совет:* замеряйте до и после включения VPN, чтобы увидеть разницу.",
        reply_markup=kb, parse_mode="Markdown"
    )

@dp.message(F.text == "🚀 ПОЛУЧИТЬ НАСТРОЙКИ")
async def send_config(message: types.Message):
    save_user(message.from_user.id)
    await bot.send_chat_action(message.chat.id, "upload_document")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                total = len(re.findall(r'vless://', content))
                caption = (
                    f"✅ **Файл конфигурации сформирован!**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🌍 Всего узлов: **{total}**\n"
                    f"🕒 Обновлено: {last_update_time}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👇 *Инструкция внутри кнопки 'Инструкция'* 👇"
                )
                await bot.send_document(
                    message.chat.id, 
                    BufferedInputFile(content.encode(), filename="proxies.txt"), 
                    caption=caption, 
                    parse_mode="Markdown"
                )

@dp.message(F.text == "📊 Статус и Пинг")
async def status_handler(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            content = await r.text() if r.status == 200 else ""
    
    hosts = re.findall(r'@([\w\.-]+):(\d+)', content)
    tasks = [check_host(h, p) for h, p in hosts]
    results = await asyncio.gather(*tasks)
    active = results.count(True)
    
    await message.answer(
        f"🖥 **МОНИТОРИНГ СЕРВЕРОВ**\n\n"
        f"📡 Доступно: `{active} / {len(hosts)}` узлов\n"
        f"🟢 Статус: **Сеть работает штатно**\n"
        f"👥 Пользователей: **{len(get_all_users())}**\n"
        f"🕒 Данные на: `{last_update_time}`", 
        parse_mode="Markdown"
    )

# --- АДМИНКА ---
@dp.message(Command("admin"))
async def admin_menu(message: types.Message):
    if message.from_user.id != USER_ID: return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="adm_br"), 
         InlineKeyboardButton(text="📊 База ID", callback_data="adm_ids")]
    ])
    await message.answer(f"👑 **Админ-центр**\nВсего юзеров: {len(get_all_users())}", reply_markup=kb)

@dp.callback_query(F.data.startswith("adm_"))
async def admin_callback(cb: CallbackQuery):
    if cb.from_user.id != USER_ID: return
    if cb.data == "adm_br":
        await cb.message.answer("Используй: `/broadcast Текст`")
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
        try: await bot.send_message(uid, f"📢 **ВАЖНОЕ УВЕДОМЛЕНИЕ:**\n\n{text}"); await asyncio.sleep(0.05)
        except: pass

# --- СИСТЕМНЫЕ ФУНКЦИИ ---
async def check_github_now():
    global last_hash, last_update_time
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PROXY_URL) as r:
                if r.status == 200:
                    c = await r.text()
                    h = hashlib.md5(c.encode()).hexdigest()
                    if h != last_hash:
                        now = datetime.now(pytz.timezone('Europe/Moscow'))
                        last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                        if last_hash != "start_node":
                            for uid in get_all_users():
                                try: await bot.send_message(uid, "🔔 **Обновление!** Добавлены новые серверы. Скачайте свежий файл."); await asyncio.sleep(0.05)
                                except: pass
                        last_hash = h
    except: pass

async def check_loop():
    while True:
        await check_github_now()
        await asyncio.sleep(60)

async def handle(request): return web.Response(text="Bot OK")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    asyncio.create_task(check_loop())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
