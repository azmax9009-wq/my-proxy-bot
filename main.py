```python
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

# --- ПАРАМЕТРЫ ДОСТУПА ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361
TARGET_USERS = [1201378326, 1180353475, 6723386873, 5209666874, 8208699361]
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = ""
last_update_time = "Синхронизация..."

# --- LUXURY КЛАВИАТУРЫ ---
def get_main_kb(user_id):
    buttons = [
        [KeyboardButton(text="✨ ПРИВАТНЫЙ ДОСТУП")],
        [KeyboardButton(text="💎 СТАТУС VIP"), KeyboardButton(text="📋 ИНФО")],
        [KeyboardButton(text="🆘 ПОДДЕРЖКА")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🛡 ПАНЕЛЬ УПРАВЛЕНИЯ")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)

def get_config_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 КОПИРОВАТЬ ВСЁ (HIDDEN)", callback_data="copy_text_hidden")],
        [InlineKeyboardButton(text="📂 СКАЧАТЬ КОНФИГ (.TXT)", callback_data="download_file")],
        [InlineKeyboardButton(text="🤳 QR-SCANNER MAX", callback_data="get_qr")]
    ])

# --- ОБРАБОТЧИКИ СОБЫТИЙ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome = (
        f"————————————————\n"
        f"🏆 **HAPP MAX PREMIUM**\n"
        f"————————————————\n\n"
        f"Приветствуем, {message.from_user.first_name}.\n"
        f"Ваш персональный шлюз безопасности готов к работе.\n\n"
        f"✨ *Все соединения зашифрованы по стандарту Reality.*"
    )
    await message.answer(welcome, reply_markup=get_main_kb(message.from_user.id), parse_mode="Markdown")

@dp.message(F.text == "✨ ПРИВАТНЫЙ ДОСТУП")
async def show_options(message: types.Message):
    await message.answer(
        "📀 **ВЫБЕРИТЕ СПОСОБ ПОЛУЧЕНИЯ ДАННЫХ:**",
        reply_markup=get_config_choice_kb()
    )

@dp.callback_query(F.data == "copy_text_hidden")
async def handle_copy_hidden(callback: CallbackQuery):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL, timeout=12) as r:
                if r.status == 200:
                    content = await r.text()
                    if not content.strip():
                        await callback.answer("⏳ База данных пуста", show_alert=True)
                        return

                    # Разбивка (Люкс формат)
                    limit = 3800
                    parts = [content[i:i+limit] for i in range(0, len(content), limit)]
                    
                    await callback.message.answer("🔒 **ВАШ КРИПТО-КАНАЛ СФОРМИРОВАН:**\n_Нажмите на блок ниже для мгновенного импорта_")
                    
                    for part in parts:
                        # Экранирование спецсимволов
                        safe_part = part.replace('\\', '\\\\').replace('`', '\\`').replace('|', '\\|')
                        # Элитный спойлер (копируется в один тап)
                        await callback.message.answer(f"||`{safe_part}`||", parse_mode="MarkdownV2")
                        await asyncio.sleep(0.3)
                else:
                    await callback.answer("📡 Сервер временно недоступен", show_alert=True)
        except:
            await callback.answer("⚠️ Ошибка защищенного соединения", show_alert=True)
    
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
                    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=600x600&margin=10&data={first}"
                    await callback.message.answer_photo(
                        qr_url, 
                        caption="📸 **SCAN & GO**\nИспользуйте встроенную камеру MAX для быстрого импорта первого узла."
                    )
        except: pass
    await callback.message.delete()
    await callback.answer()

@dp.message(F.text == "💎 СТАТУС VIP")
async def status_handler(message: types.Message):
    start = time.time()
    status_icon = "⚪️"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://google.com", timeout=3):
                ping = round((time.time() - start) * 1000)
                status_icon = "🟢" if ping < 300 else "🟡"
                res = f"{status_icon} **СЕРВЕРЫ АКТИВНЫ**"
    except: 
        res = "🔴 **СЕРВИС НА ОБСЛУЖИВАНИИ**"
        ping = "N/A"
    
    await message.answer(
        f"📊 **HAPP MAX MONITORING**\n\n"
        f"▪️ Статус: {res}\n"
        f"▪️ Пинг узла: `{ping} ms`\n"
        f"▪️ Синхронизация: `{last_update_time}`", 
        parse_mode="Markdown"
    )

@dp.message(F.text == "🆘 ПОДДЕРЖКА")
async def support_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 НАПИСАТЬ КОНСЬЕРЖУ", url=f"tg://user?id={ADMIN_ID}")]])
    await message.answer("Требуется помощь в настройке или оплате?\nНаш специалист ответит в кратчайшие сроки.", reply_markup=kb)

# --- МОНИТОРИНГ GITHUB (ПРЕМИУМ ЛОГИКА) ---
async def check_github_loop():
    global last_hash, last_update_time
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL, timeout=15) as r:
                    if r.status == 200:
                        content = await r.text()
                        new_hash = hashlib.md5(content.encode()).hexdigest()
                        if new_hash != last_hash:
                            last_update_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime("%H:%M:%S (%d/%m)")
                            if last_hash != "":
                                for uid in TARGET_USERS:
                                    try: 
                                        await bot.send_message(uid, "💎 **HAPP MAX UPDATE**\n\nВаши ключи доступа были обновлены. Пожалуйста, получите актуальные конфигурации.")
                                    except: pass
                            last_hash = new_hash
        except: pass
        await asyncio.sleep(60)

# --- WEB-ХУК / ЖИЗНЬ ---
async def handle(request): return web.Response(text="Happ Luxury Edition")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(check_github_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

```
