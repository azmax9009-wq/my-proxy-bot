import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание сканирования..."

def get_main_keyboard():
    kb = [
        [KeyboardButton(text="🚀 Получить прокси")],
        [KeyboardButton(text="📖 Инструкция")],
        [KeyboardButton(text="ℹ️ О боте")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as resp:
                if resp.status == 200:
                    return (await resp.text()).strip()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    return None

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "👋 **Добро пожаловать!**\n\n"
        "Я помогу вам настроить быстрый интернет.\n"
        "Нажмите кнопку **«🚀 Получить прокси»**, чтобы забрать файл, "
        "или **«📖 Инструкция»**, чтобы узнать, как всё настроить."
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    help_text = (
        "👵👴 **ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:**\n\n"
        "1️⃣ **Установите приложение Hiddify:**\n"
        "📱 **Для Android:** [Play Market](https://play.google.com/store/apps/details?id=app.hiddify.com)\n"
        "🍎 **Для iPhone:** [App Store](https://apps.apple.com/us/app/hiddify-next/id6473777529)\n\n"
        "2️⃣ **Как запустить интернет:**\n"
        "• Нажмите кнопку **«🚀 Получить прокси»** здесь.\n"
        "• Скопируйте текст из файла, который я пришлю.\n"
        "• В приложении Hiddify нажмите **«Новый профиль»** (+).\n"
        "• Нажмите **«Добавить из буфера»**.\n"
        "• Нажмите круглую кнопку в центре. Она станет **зеленой**.\n\n"
        "✅ **Все готово!**"
    )
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    about_text = (
        f"🤖 **Статус:** Работаю\n"
        f"🕒 **Последнее обновление данных:** `{last_update_time}`\n\n"
        "Я проверяю новые настройки каждую минуту. Если они изменятся, я сразу пришлю вам уведомление."
    )
    await message.answer(about_text, parse_mode="Markdown")

@dp.message(F.text == "🚀 Получить прокси")
@dp.message(Command("test"))
async def manual_test(message: types.Message):
    proxies = await get_proxies()
    if proxies:
        caption = f"📄 Ваши настройки готовы!\n🕒 Время обновления: {last_update_time}"
        file_data = proxies.encode('utf-8')
        input_file = BufferedInputFile(file_data, filename="proxies.txt")
        await bot.send_document(message.chat.id, input_file, caption=caption)
    else:
        await message.answer("❌ Ошибка связи. Пожалуйста, попробуйте еще раз через минуту.")

async def check_proxies_loop():
    global last_hash, last_update_time
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                new_time_str = now.strftime("%H:%M:%S (%d.%m.%Y)")
                if last_hash != "start_node":
                    last_update_time = new_time_str
                    msg = "🔔 **Внимание! Появились новые настройки прокси.**\nНажмите кнопку «🚀 Получить прокси» ниже."
                    await bot.send_message(USER_ID, msg, parse_mode="Markdown")
                else:
                    last_update_time = new_time_str
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Running"))
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', int(os.getenv("PORT", 10000))).start()

async def main():
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
