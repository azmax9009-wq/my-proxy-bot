import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz # Нужно для правильного времени
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_hash = "start_node"
last_update_time = "Неизвестно"

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text.strip()
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
    return None

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "👋 **Привет! Я монитор прокси.**\n\n"
        "✅ Я слежу за обновлениями 24/7.\n"
        "🔔 Когда прокси обновятся, я пришлю уведомление.\n"
        "📄 Чтобы получить актуальный файл прямо сейчас, напиши /test.\n\n"
        f"🕒 Последнее обновление было: `{last_update_time}`"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("test"))
async def manual_test(message: types.Message):
    proxies = await get_proxies()
    if proxies:
        caption = f"📄 Полный список прокси\n🕒 Обновлено: {last_update_time}"
        file_data = proxies.encode('utf-8')
        input_file = BufferedInputFile(file_data, filename="proxies.txt")
        await bot.send_document(message.chat.id, input_file, caption=caption)
    else:
        await message.answer("❌ Ошибка загрузки прокси.")

async def check_proxies_loop():
    global last_hash, last_update_time
    print("Мониторинг запущен...")
    
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            if current_hash != last_hash:
                # Устанавливаем время (МСК)
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                last_update_time = now.strftime("%H:%M:%S (%d.%m.%Y)")
                
                if last_hash != "start_node":
                    # Уведомление об обновлении без файла
                    msg = (
                        "🔔 **ОБНАРУЖЕНЫ НОВЫЕ ПРОКСИ!**\n\n"
                        f"🕒 Время обновления: `{last_update_time}` МСК\n"
                        "👉 Введи команду /test, чтобы получить свежий файл."
                    )
                    await bot.send_message(USER_ID, msg, parse_mode="Markdown")
                
                last_hash = current_hash
            else:
                print("Изменений нет...")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Бот в сети"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

async def main():
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
