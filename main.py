import asyncio
import aiohttp
import hashlib
import os
from aiogram import Bot, Dispatcher

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
USER_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt'
CHECK_INTERVAL = 60 # Проверка раз в минуту

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
                        content = await resp.text()
                        # Убираем лишние пробелы по краям
                        content = content.strip()
                        current_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        if current_hash != last_hash:
                            if last_hash != "":
                                # Оформляем весь список одним блоком для удобного копирования
                                text = f"🚀 **Список прокси обновлен!**\n\n```\n{content}\n```"
                                # Если текст слишком длинный (больше 4096 символов), Telegram его не примет
                                if len(text) > 4000:
                                    text = f"🚀 **Прокси (часть 1):**\n\n
http://googleusercontent.com/immersive_entry_chip/0

### Почему так лучше:
1.  **MarkdownV2 и кавычки 
http://googleusercontent.com/immersive_entry_chip/1
