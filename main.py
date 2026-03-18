import asyncio
import aiohttp
import hashlib
import os
from aiogram import Bot, Dispatcher

# --- ТВОИ НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 # Проверка каждые 10 минут

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_hash = ""

async def check_proxies():
    global last_hash
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(PROXY_URL) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        current_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if current_hash != last_hash:
                            if last_hash != "":
                                # Шлем уведомление, если файл изменился
                                text = f"🚀 **Обновление прокси!**\n\n`{content[:3500]}`"
                                await bot.send_message(USER_ID, text, parse_mode="Markdown")
                            last_hash = current_hash
            except Exception as e:
                print(f"Ошибка: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Бот в строю!"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    print("Бот запущен и следит за прокси...")
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
