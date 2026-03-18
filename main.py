import asyncio
import aiohttp
import hashlib
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_hash = ""

async def get_proxies():
    """Функция для скачивания и очистки прокси"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PROXY_URL) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    return "\n".join(lines)
        except Exception as e:
            print(f"Ошибка при загрузке: {e}")
    return None

def format_message(content, title="🚀 Список прокси"):
    """Форматирует сообщение для копирования по клику"""
    header = f"**{title}**\n\n"
    # Ограничение длины для Telegram
    if len(content) > 3800:
        content = content[:3800] + "\n...список обрезан..."
    return f"{header}```\n{content}\n```"

@dp.message(Command("test"))
async def send_test_proxies(message: types.Message):
    """Ответ на команду /test"""
    proxies = await get_proxies()
    if proxies:
        await message.answer(format_message(proxies, "📊 Текущие прокси из файла:"), parse_mode="MarkdownV2")
    else:
        await message.answer("❌ Не удалось загрузить прокси.")

async def check_proxies_loop():
    """Фоновая проверка обновлений"""
    global last_hash
    print("Мониторинг запущен...")
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            if current_hash != last_hash:
                if last_hash != "":
                    text = format_message(content, "🔔 ОБНОВЛЕНИЕ!")
                    await bot.send_message(USER_ID, text, parse_mode="MarkdownV2")
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
    print("--- ЗАПУСК СИСТЕМЫ ---")
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    print("Бот в сети. Напиши /test в Telegram.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
