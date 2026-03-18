import asyncio
import aiohttp
import hashlib
import os
from aiogram import Bot, Dispatcher

# --- НАСТРОЙКИ ---
# Токен твоего бота из BotFather
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
# Твой личный ID (куда слать уведомления)
USER_ID = 8208699361 
# Ссылка на файл с прокси на GitHub (сырой текст)
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
# Интервал проверки в секундах (60 = 1 минута)
CHECK_INTERVAL = 60 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
last_hash = ""

async def check_proxies():
    global last_hash
    print("Проверка прокси запущена...")
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(PROXY_URL) as resp:
                    if resp.status == 200:
                        raw_content = await resp.text()
                        
                        # Очистка: убираем пустые строки и лишние пробелы
                        lines = [line.strip() for line in raw_content.splitlines() if line.strip()]
                        clean_content = "\n".join(lines)
                        
                        # Хэш для проверки изменений
                        current_hash = hashlib.md5(clean_content.encode()).hexdigest()
                        
                        if current_hash != last_hash:
                            if last_hash != "":
                                # Формируем заголовок и само тело прокси
                                header = "🚀 **Список прокси обновлен!**\n\n"
                                code_block = f"```\n{clean_content}\n```"
                                
                                # Проверка лимита Telegram (4096 символов)
                                if len(header + code_block) > 4090:
                                    # Если слишком длинно, берем сколько влезет
                                    short_content = clean_content[:3800] + "\n...список слишком длинный..."
                                    text = f"{header}```\n{short_content}\n```"
                                else:
                                    text = header + code_block
                                
                                # Отправляем с MarkdownV2 (важно для копирования по клику)
                                # Экранируем спецсимволы для MarkdownV2 (упрощенно для блоков кода)
                                await bot.send_message(USER_ID, text, parse_mode="MarkdownV2")
                                print("Сообщение с обновлением отправлено!")
                                
                            last_hash = current_hash
            except Exception as e:
                print(f"Ошибка при проверке: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    """Заглушка для того, чтобы Render не закрывал порт"""
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Бот активен"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-заглушка запущена на порту {port}")

async def main():
    print("--- ИНИЦИАЛИЗАЦИЯ ЗАПУСКА ---")
    # Запускаем фоновые задачи
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies())
    print("Бот запущен и следит за прокси...")
    # Запускаем прослушивание (бот в сети)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
