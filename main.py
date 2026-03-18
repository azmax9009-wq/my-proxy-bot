import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BufferedInputFile

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 # Проверка каждую минуту

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Глобальные переменные для памяти бота
last_hash = "start_node"
last_update_time = "Ожидание первого сканирования..."

async def get_proxies():
    """Скачивает текст прокси с GitHub"""
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
    """Описание бота и памятка"""
    welcome_text = (
        "👋 **Привет! Я твой монитор прокси.**\n\n"
        "✅ Я слежу за обновлениями в репозитории 24/7.\n"
        "🔔 Когда появятся новые прокси, я пришлю уведомление.\n\n"
        "📌 **Памятка:**\n"
        "Если уведомление пришло (или если хочешь проверить вручную) — пиши команду /test. "
        "Я пришлю актуальный список полным файлом.\n\n"
        f"🕒 Последнее зафиксированное обновление: `{last_update_time}`"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("test"))
async def manual_test(message: types.Message):
    """Отправка прокси файлом по запросу"""
    proxies = await get_proxies()
    if proxies:
        caption = f"📄 Полный список прокси\n🕒 По состоянию на: {last_update_time}"
        file_data = proxies.encode('utf-8')
        input_file = BufferedInputFile(file_data, filename="proxies.txt")
        await bot.send_document(message.chat.id, input_file, caption=caption)
    else:
        await message.answer("❌ Не удалось загрузить прокси. Проверь ссылку или интернет.")

async def check_proxies_loop():
    """Фоновый цикл мониторинга обновлений"""
    global last_hash, last_update_time
    print("Мониторинг запущен...")
    
    while True:
        content = await get_proxies()
        if content:
            current_hash = hashlib.md5(content.encode()).hexdigest()
            
            # Если содержимое изменилось
            if current_hash != last_hash:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                new_time_str = now.strftime("%H:%M:%S (%d.%m.%Y)")

                # Если это НЕ первый запуск бота (реальное обновление)
                if last_hash != "start_node":
                    last_update_time = new_time_str
                    msg = (
                        "🔔 **ОБНАРУЖЕНЫ НОВЫЕ ПРОКСИ!**\n\n"
                        f"🕒 Время обновления: `{last_update_time}` МСК\n"
                        "👉 Введи команду /test, чтобы получить свежий файл."
                    )
                    await bot.send_message(USER_ID, msg, parse_mode="Markdown")
                    print(f"Отправлено уведомление об обновлении: {last_update_time}")
                else:
                    # При самом первом запуске просто запоминаем текущее состояние
                    last_update_time = new_time_str
                    print(f"Первый запуск: база данных синхронизирована ({last_update_time})")
                
                last_hash = current_hash
            else:
                print("Изменений на GitHub нет, ждем...")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    """Заглушка для Render, чтобы сервис не засыпал"""
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Бот активен 24/7"))
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    await web.TCPSite(runner, '0.0.0.0', port).start()

async def main():
    print("--- ЗАПУСК БОТА ---")
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
