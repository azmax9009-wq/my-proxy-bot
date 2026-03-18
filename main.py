import asyncio
import aiohttp
import hashlib
import os
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
last_hash = ""

async def get_proxies():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text.strip()
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
    return None

async def send_as_file(chat_id, content, caption):
    """Функция для отправки текста в виде .txt файла"""
    file_data = content.encode('utf-8')
    input_file = BufferedInputFile(file_data, filename="proxies.txt")
    await bot.send_document(chat_id, input_file, caption=caption)

@dp.message(Command("test"))
async def send_test_proxies(message: types.Message):
    proxies = await get_proxies()
    if proxies:
        await send_as_file(message.chat.id, proxies, "📄 Вот полный список прокси (одним файлом)")
    else:
        await message.answer("❌ Не удалось загрузить прокси.")

async def check_proxies_loop():
    global last_hash
    print("Мониторинг запущен...")
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                if last_hash != "":
                    await send_as_file(USER_ID, content, "🔔 ОБНОВЛЕНИЕ! Весь список в файле выше.")
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="OK"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

async def main():
    print("--- ЗАПУСК СИСТЕМЫ (TXT MODE) ---")
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    print("Бот в сети. Напиши /test для получения файла.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
