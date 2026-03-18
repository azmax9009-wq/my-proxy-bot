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
USERS_FILE = "users_list.txt"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_hash = "start_node"
last_update_time = "Ожидание сканирования..."

# --- ФУНКЦИИ БАЗЫ ДАННЫХ (ФАЙЛ) ---
def save_user(user_id):
    """Сохраняет ID пользователя в файл"""
    user_id_str = str(user_id)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            f.write(user_id_str + "\n")
        return True
    
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    
    if user_id_str not in users:
        with open(USERS_FILE, "a") as f:
            f.write(user_id_str + "\n")
        return True
    return False

def get_all_users():
    """Получает всех пользователей для рассылки"""
    if not os.path.exists(USERS_FILE):
        return [USER_ID]
    with open(USERS_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

async def notify_admin(user: types.User, action: str):
    """Уведомление тебе об активности других"""
    if user.id != USER_ID:
        info = f"👤 **Активность:**\n• Имя: {user.full_name}\n• ID: `{user.id}`\n• Действие: {action}"
        try:
            await bot.send_message(USER_ID, info, parse_mode="Markdown")
        except: pass

# --- КЛАВИАТУРА ---
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
        except: pass
    return None

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    is_new = save_user(message.from_user.id)
    action = "Запустил бота (НОВЫЙ!)" if is_new else "Запустил бота снова"
    await notify_admin(message.from_user, action)
    
    welcome_text = (
        "👋 **Добро пожаловать!**\n\n"
        "Я слежу за обновлением прокси 24/7.\n"
        "Нажмите кнопку **«🚀 Получить прокси»**, чтобы забрать файл.\n"
        "Если вы новичок, нажмите **«📖 Инструкция»**."
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(F.text == "📖 Инструкция")
async def send_help(message: types.Message):
    await notify_admin(message.from_user, "Смотрит инструкцию")
    help_text = (
        "👵👴 **ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:**\n\n"
        "1️⃣ **Установите приложение Hiddify:**\n"
        "📱 **Android:** [Play Market](https://play.google.com/store/apps/details?id=app.hiddify.com)\n"
        "🍎 **iPhone:** [App Store](https://apps.apple.com/us/app/hiddify-next/id6473777529)\n\n"
        "2️⃣ **Как запустить интернет:**\n"
        "• Нажмите кнопку **«🚀 Получить прокси»** здесь.\n"
        "• Скопируйте текст из файла, который я пришлю.\n"
        "• В приложении Hiddify нажмите **«Новый профиль»** (+).\n"
        "• Выберите **«Добавить из буфера»**.\n"
        "• Нажмите круглую кнопку в центре. Она станет **зеленой**.\n\n"
        "✅ **Все готово!**"
    )
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message(F.text == "ℹ️ О боте")
async def about_bot(message: types.Message):
    await notify_admin(message.from_user, "Смотрит статус бота")
    about_text = (
        f"🤖 **Статус:** Работаю стабильно\n"
        f"🕒 **Данные обновлены:** `{last_update_time}`\n\n"
        "Я автоматически рассылаю новые настройки всем пользователям."
    )
    await message.answer(about_text, parse_mode="Markdown")

@dp.message(F.text == "🚀 Получить прокси")
@dp.message(Command("test"))
async def manual_test(message: types.Message):
    save_user(message.from_user.id)
    await notify_admin(message.from_user, "Запросил прокси")
    proxies = await get_proxies()
    if proxies:
        caption = f"📄 Ваши настройки!\n🕒 Актуально на: {last_update_time}"
        file_data = proxies.encode('utf-8')
        input_file = BufferedInputFile(file_data, filename="proxies.txt")
        await bot.send_document(message.chat.id, input_file, caption=caption)
    else:
        await message.answer("❌ Ошибка. Попробуйте нажать кнопку еще раз.")

# --- ЦИКЛ ПРОВЕРКИ И РАССЫЛКИ ---
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
                    msg = f"🔔 **НОВЫЕ ПРОКСИ!**\n🕒 Обновлено в: `{last_update_time}` МСК\nНажмите «🚀 Получить прокси», чтобы скачать файл."
                    
                    # Массовая рассылка всем пользователям из списка
                    all_users = get_all_users()
                    for uid in all_users:
                        try:
                            await bot.send_message(uid, msg, parse_mode="Markdown")
                            await asyncio.sleep(0.1) # Чтобы телеграм не забанил за скорость
                        except: continue
                else:
                    last_update_time = new_time_str
                last_hash = current_hash
        await asyncio.sleep(CHECK_INTERVAL)

async def web_stub():
    from aiohttp import web
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot Online"))
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', int(os.getenv("PORT", 10000))).start()

async def main():
    asyncio.create_task(web_stub())
    asyncio.create_task(check_proxies_loop())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
