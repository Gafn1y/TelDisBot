import disnake
import asyncio
import os
from disnake.ext import commands
from telegram.ext import Application

# Токены
DISCORD_TOKEN = "token"
TELEGRAM_TOKEN = "token"
TELEGRAM_CHAT_ID = "id"

# Файлы для отслеживания
TRACKED_CHANNELS_FILE = "tracked_channels.txt"
TRACKED_USERS_FILE = "tracked_users.txt"
TRACKED_CHANNELS = []
TRACKED_USERS = []

# Функция для загрузки отслеживаемых каналов из файла
def load_tracked_channels():
    if os.path.exists(TRACKED_CHANNELS_FILE):
        with open(TRACKED_CHANNELS_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

# Функция для загрузки отслеживаемых пользователей из файла
def load_tracked_users():
    if os.path.exists(TRACKED_USERS_FILE):
        with open(TRACKED_USERS_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

# Функция для сохранения канала в файл
def save_tracked_channel(channel_id: str):
    with open(TRACKED_CHANNELS_FILE, "a") as f:
        f.write(f"{channel_id}\n")

# Функция для сохранения пользователя в файл
def save_tracked_user(user_id: str):
    with open(TRACKED_USERS_FILE, "a") as f:
        f.write(f"{user_id}\n")

# Функция для удаления канала из списка и файла
def remove_tracked_channel(channel_id: str):
    global TRACKED_CHANNELS
    TRACKED_CHANNELS = [ch for ch in TRACKED_CHANNELS if ch != channel_id]
    with open(TRACKED_CHANNELS_FILE, "w") as f:
        for ch in TRACKED_CHANNELS:
            f.write(f"{ch}\n")

# Функция для удаления пользователя из списка и файла
def remove_tracked_user(user_id: str):
    global TRACKED_USERS
    TRACKED_USERS = [usr for usr in TRACKED_USERS if usr != user_id]
    with open(TRACKED_USERS_FILE, "w") as f:
        for usr in TRACKED_USERS:
            f.write(f"{usr}\n")

# Загружаем отслеживаемые каналы и пользователей
TRACKED_CHANNELS = load_tracked_channels()
TRACKED_USERS = load_tracked_users()

# Настройка Telegram-бота
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Настройка Discord-бота
intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True  # Включаем разрешение на чтение сообщений!

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен и работает!")

# ======= КОМАНДЫ БОТА =======

@bot.command(name="list_tracked")
async def list_tracked(ctx):
    """Показать список отслеживаемых пользователей и каналов"""
    if not TRACKED_CHANNELS and not TRACKED_USERS:
        await ctx.send("📋 Список отслеживаемых пуст.")
        return

    tracked_channels_str = "\n".join(f"<#{ch}>" for ch in TRACKED_CHANNELS) if TRACKED_CHANNELS else "Нет отслеживаемых каналов."
    tracked_users_str = "\n".join(f"<@{usr}>" for usr in TRACKED_USERS) if TRACKED_USERS else "Нет отслеживаемых пользователей."

    message = (f"📋 **Список отслеживаемых**:\n\n"
               f"**Каналы:**\n{tracked_channels_str}\n\n"
               f"**Пользователи:**\n{tracked_users_str}")

    await ctx.send(message)

@bot.command(name="add_channel")
async def add_channel(ctx, channel: disnake.TextChannel):
    """Добавить канал в список отслеживаемых"""
    channel_id_str = str(channel.id)
    if channel_id_str not in TRACKED_CHANNELS:
        TRACKED_CHANNELS.append(channel_id_str)
        save_tracked_channel(channel_id_str)
        await ctx.send(f"✅ Канал {channel.mention} добавлен в список отслеживаемых.")
    else:
        await ctx.send(f"⚠️ Канал {channel.mention} уже отслеживается.")

@bot.command(name="remove_channel")
async def remove_channel(ctx, channel: disnake.TextChannel):
    """Удалить канал из списка отслеживаемых"""
    channel_id_str = str(channel.id)
    if channel_id_str in TRACKED_CHANNELS:
        remove_tracked_channel(channel_id_str)
        await ctx.send(f"✅ Канал {channel.mention} удален из списка отслеживаемых.")
    else:
        await ctx.send(f"⚠️ Канал {channel.mention} не найден в списке.")

@bot.command(name="add_user")
async def add_user(ctx, user: disnake.Member):
    """Добавить пользователя в список отслеживаемых"""
    user_id_str = str(user.id)
    if user_id_str not in TRACKED_USERS:
        TRACKED_USERS.append(user_id_str)
        save_tracked_user(user_id_str)
        await ctx.send(f"✅ Пользователь {user.mention} добавлен в список отслеживаемых.")
    else:
        await ctx.send(f"⚠️ Пользователь {user.mention} уже отслеживается.")

@bot.command(name="remove_user")
async def remove_user(ctx, user: disnake.Member):
    """Удалить пользователя из списка отслеживаемых"""
    user_id_str = str(user.id)
    if user_id_str in TRACKED_USERS:
        remove_tracked_user(user_id_str)
        await ctx.send(f"✅ Пользователь {user.mention} удален из списка отслеживаемых.")
    else:
        await ctx.send(f"⚠️ Пользователь {user.mention} не найден в списке.")

# ======= ОБРАБОТКА СООБЩЕНИЙ =======

@bot.event
async def on_message(message: disnake.Message):
    """Обрабатывает сообщения и пересылает их в Telegram, если они из отслеживаемых каналов"""
    if message.author.bot:
        return  # Игнорируем сообщения от ботов

    print(f"📩 Получено сообщение: {message.content} от {message.author}")  # Логируем сообщение

    if str(message.channel.id) in TRACKED_CHANNELS and str(message.author.id) in TRACKED_USERS:
        text = f"📩 Сообщение из Discord\n👤 От: {message.author}\n💬 {message.content}"
        asyncio.create_task(send_to_telegram(text))

    await bot.process_commands(message)  # Без этого команды не будут работать!

async def send_to_telegram(text):
    """Отправляет сообщение в Telegram"""
    await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)

# Запуск бота
bot.run(DISCORD_TOKEN)