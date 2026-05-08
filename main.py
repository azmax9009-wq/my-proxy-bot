import asyncio
import aiohttp
import hashlib
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- НАСТРОЙКИ ---
API_TOKEN = '8459395402:AAEBWV85J1rUMxu825hvnHzd1SHtaDG8xoc'
ADMIN_ID = 8208699361 
PROXY_URL = 'https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/WHITE-CIDR-RU-checked.txt'
USERS_FILE = "users_list.txt"

# Картинки
START_PIC = "https://w.forfun.com/fetch/1f/1f81d113426e2a149a4a755d506927d1.jpeg"
ADMIN_PIC = "https://img.goodfon.ru/original/1920x1080/7/da/mariya-s-shlemom-art-kiberpank-pogranichnik-cyberpunk.jpg"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Переменная для слежки за обновлением (хеш файла)
LAST_FILE_HASH = None

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def save_user(user_id):
    """Сохраняет ID пользователя в файл, если его там нет"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f: pass

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")
        return True
    return False

async def admin_notify(text):
    """Уведомление админа в ЛС"""
    try:
        await bot.send_message(ADMIN_ID, f"🛠 **LOG:** {text}", parse_mode="Markdown")
    except: pass

def clean_for_iphone(text):
    """Фильтр: только рабочие протоколы для iOS"""
    valid = ('vless://', 'ss://', 'trojan://', 'vmess://', 'hysteria2://', 'tuic://')
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith(valid)]
    return "\n".join(lines)

# --- КЛАВИАТУРЫ ---

def get_main_kb():
    kb = [
        [KeyboardButton(text="📱 Получить Конфиг")],
        [KeyboardButton(text="📸 QR-Код"), KeyboardButton(text="📊 Статус")],
        [KeyboardButton(text="🛡 Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_file_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍏 iPhone (.txt)", callback_data="f_iphone")],
        [InlineKeyboardButton(text="🤖 Android / PC", callback_data="f_android")]
    ])

# --- ФОНОВАЯ ЗАДАЧА: ПРОВЕРКА ОБНОВЛЕНИЙ ---

async def auto_update_checker():
    """Каждые 10 минут проверяет GitHub на наличие новых прокси"""
    global LAST_FILE_HASH
    print("🛰 Система мониторинга запущена...")
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(PROXY_URL) as r:
                    if r.status == 200:
                        content = await r.text()
                        current_hash = hashlib.md5(content.encode()).hexdigest()

                        # Если хеш изменился — рассылаем всем
                        if LAST_FILE_HASH is not None and current_hash != LAST_FILE_HASH:
                            LAST_FILE_HASH = current_hash
                            await broadcast_new_proxies(content)
                        else:
                            LAST_FILE_HASH = current_hash
        except Exception as e:
            print(f"Ошибка проверки: {e}")
        
        await asyncio.sleep(600) # Проверка раз в 10 минут

async def broadcast_new_proxies(content):
    """Рассылает новый файл всем пользователям из базы"""
    if not os.path.exists(USERS_FILE): return

    with open(USERS_FILE, "r") as f:
        user_ids = f.read().splitlines()

    iphone_data = clean_for_iphone(content).encode()
    sent_count = 0

    for uid in user_ids:
        try:
            await bot.send_message(uid, "🔔 **Внимание! Обновление прокси!**\nМы нашли новые рабочие сервера. Держи свежий список:")
            await bot.send_document(
                uid, 
                BufferedInputFile(iphone_data, filename="Auto_Update_iOS.txt"),
                caption="🍏 Обновлено автоматически"
            )
            sent_count += 1
            await asyncio.sleep(0.05) # Чтобы не словить бан за спам
        except:
            pass
    
    await admin_notify(f"Авто-рассылка завершена. Обновились {sent_count} чел.")

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    save_user(message.from_user.id)
    msg = "🔥 **Happ VPN Online**\n\nЯ автоматически пришлю тебе новые прокси, как только они появятся!\n\nИли выбери формат сейчас:"
    try:
        await bot.send_photo(message.chat.id, START_PIC, caption=msg, reply_markup=get_main_kb(), parse_mode="Markdown")
    except:
        await message.answer(msg, reply_markup=get_main_kb(), parse_mode="Markdown")

@dp.message(F.text == "📱 Получить Конфиг")
async def config_menu(message: types.Message):
    await message.answer("🛠 **Выбери формат файла:**", reply_markup=get_file_kb())

@dp.callback_query(F.data.startswith("f_"))
async def send_file(callback: types.CallbackQuery):
    await callback.answer("Загрузка...")
    async with aiohttp.ClientSession() as session:
        async with session.get(PROXY_URL) as r:
            if r.status == 200:
                content = await r.text()
                if callback.data == "f_iphone":
                    final_data = clean_for_iphone(content)
                    filename = "iPhone_Configs.txt"
                else:
                    final_data = content
                    filename = "Full_Configs.txt"

                await bot.send_document(
                    callback.message.chat.id,
                    BufferedInputFile(final_data.encode(), filename=filename),
                    caption="📄 Твой файл с конфигами"
                )

@dp.message(F.text == "📊 Статус")
async def status_check(message: types.Message):
    await message.answer("🛰 Система: `Online`\n📡 Авто-рассылка: `Активна`", parse_mode="Markdown")

# --- АДМИНКА ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        count = 0
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f: count = len(f.readlines())
        await bot.send_photo(message.chat.id, ADMIN_PIC, caption=f"👑 **АДМИНКА**\n\nЮзеров: `{count}`")

# --- ЗАПУСК ---

async def handle_web(request): 
    return web.Response(text="Bot is running")

async def main():
    # Запускаем фоновую задачу
    asyncio.create_task(auto_update_checker())

    # Настройка веб-сервера (для деплоя)
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        print("Бот выключен")