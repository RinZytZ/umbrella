import discord
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = 991057181677850694  # Ваш ID, мистер Вескер
LOG_CHANNEL_ID = 123456789012345678  # ID канала для логов слежки (укажите свой)

# Файлы для хранения
BLACKLIST_FILE = "blacklist.json"
CHAT_SESSIONS_FILE = "chat_sessions.json"

# Загружаем данные
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

blacklist = load_json(BLACKLIST_FILE, [])
chat_sessions = load_json(CHAT_SESSIONS_FILE, {})

# Данные слежки (в оперативной памяти)
watched_users = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def is_blacklisted(user_id):
    return user_id in blacklist

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_watched(user_id):
    return user_id in watched_users

async def log_to_channel(message_text):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(message_text)

async def log_to_admin(message_text):
    try:
        admin = await bot.fetch_user(ADMIN_ID)
        await admin.send(message_text)
    except:
        pass

# ==================== СОБЫТИЯ ====================
@bot.event
async def on_ready():
    print(f"☂️ МОГ-Зонт активирован: {bot.user}")
    print(f"Слежка: {len(watched_users)} целей")
    print(f"Чёрный список: {len(blacklist)}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Обработка ЛС
    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        
        if is_blacklisted(user_id):
            await message.author.send("☂️ `Доступ заблокирован.`")
            return
        
        # !старт
        if message.content.strip() == "!старт":
            embed = discord.Embed(
                title="☂️ **UMBRELLA CORPORATION**",
                description="**МОБИЛЬНАЯ ОПЕРАТИВНАЯ ГРУППА «ЗОНТ»**",
                color=discord.Color.dark_red()
            )
            embed.add_field(name="Статус", value="Активирована", inline=True)
            embed.add_field(name="Ваш ID", value=f"`{user_id}`", inline=True)
            embed.add_field(name="Инструкция", value="Введите `!терминал` для списка команд", inline=False)
            await message.author.send(embed=embed)
            return
        
        # !терминал
        if message.content.strip() == "!терминал":
            await show_terminal(message.author)
            return
        
        # !связь
        if message.content.strip() == "!связь":
            await message.author.send("☂️ Система: **ОНЛАЙН**")
            return
        
        # !связаться <ID> <текст>
        if message.content.startswith("!связаться"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.author.send("☂️ Использование: `!связаться <ID> <текст>`")
                return
            
            try:
                target_id = int(parts[1])
                text = parts[2]
                target = await bot.fetch_user(target_id)
                
                embed = discord.Embed(
                    title="☂️ **АНОНИМНОЕ СООБЩЕНИЕ**",
                    description=text,
                    color=discord.Color.dark_red()
                )
                await target.send(embed=embed)
                
                chat_sessions[target_id] = {"partner_id": user_id, "started": datetime.now().isoformat()}
                save_json(CHAT_SESSIONS_FILE, chat_sessions)
                
                await message.author.send(f"☂️ Сообщение отправлено ID: {target_id}")
                await log_to_admin(f"Анонимный чат: {message.author.name} -> {target.name}: {text}")
            except:
                await message.author.send("☂️ Ошибка: пользователь не найден")
            return
        
        # !канал <ID> <текст>
        if message.content.startswith("!канал"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.author.send("☂️ Использование: `!канал <ID_канала> <текст>`")
                return
            
            try:
                channel_id = int(parts[1])
                text = parts[2]
                channel = bot.get_channel(channel_id)
                
                if channel:
                    await channel.send(f"☂️ **{text}**")
                    await message.author.send(f"☂️ Отправлено в {channel.name}")
                else:
                    await message.author.send("☂️ Канал не найден")
            except:
                await message.author.send("☂️ Ошибка")
            return
        
        # Ответ в анонимном чате
        if user_id in chat_sessions:
            partner_id = chat_sessions[user_id]["partner_id"]
            try:
                partner = await bot.fetch_user(partner_id)
                await partner.send(f"☂️ **Ответ:**\n{message.content}")
                await log_to_admin(f"Ответ в чате: {message.author.name} -> {partner.name}: {message.content}")
            except:
                pass
            return
        
        await message.author.send("☂️ Неизвестная команда. Введите `!терминал`")
        return
    
    # Серверные сообщения (слежка)
    if message.guild:
        if is_watched(message.author.id):
            await log_to_channel(
                f"☂️ **СООБЩЕНИЕ**\n"
                f"👤 {message.author.name}\n"
                f"📝 {message.content[:500]}"
            )
    
    await bot.process_commands(message)

# ==================== СОБЫТИЯ СЛЕЖКИ ====================
@bot.event
async def on_presence_update(before, after):
    if after.guild and is_watched(after.id):
        if before.status != after.status:
            await log_to_channel(f"☂️ **СТАТУС** {after.name}: {before.status} → {after.status}")

@bot.event
async def on_voice_state_update(member, before, after):
    if is_watched(member.id):
        if before.channel is None and after.channel is not None:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} зашёл в {after.channel.name}")
        elif before.channel is not None and after.channel is None:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} вышел из {before.channel.name}")

@bot.event
async def on_member_join(member):
    if is_watched(member.id):
        await log_to_channel(f"☂️ **ВХОД** {member.name} зашёл на сервер {member.guild.name}")

# ==================== КОМАНДЫ ДЛЯ ВСЕХ ====================
@bot.command(name="слежка")
async def start_surveillance(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    
    try:
        target = await bot.fetch_user(user_id)
        if user_id in watched_users:
            await ctx.send(f"☂️ Слежка за {target.name} уже активна")
            return
        
        watched_users[user_id] = {"username": target.name, "added": datetime.now().isoformat(), "started_by": ctx.author.id}
        await ctx.send(f"☂️ Слежка за {target.name} активирована")
        await log_to_channel(f"☂️ Слежка начата: {target.name} (инициатор: {ctx.author.name})")
    except:
        await ctx.send("☂️ Пользователь не найден")

@bot.command(name="снятьслежку")
async def stop_surveillance(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    
    if user_id not in watched_users:
        await ctx.send(f"☂️ Слежка за ID {user_id} не активна")
        return
    
    target_name = watched_users[user_id]["username"]
    del watched_users[user_id]
    await ctx.send(f"☂️ Слежка за {target_name} прекращена")

@bot.command(name="списокцелей")
async def list_targets(ctx):
    if is_blacklisted(ctx.author.id):
        return
    
    if not watched_users:
        await ctx.send("☂️ Нет активных целей")
        return
    
    targets = "\n".join([f"👤 {data['username']} (ID: {uid})" for uid, data in watched_users.items()])
    await ctx.send(f"☂️ **Цели слежки:**\n{targets}")

# ==================== АДМИН-КОМАНДЫ ====================
@bot.command(name="ликвидировать")
async def liquidate(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    
    if user_id not in blacklist:
        blacklist.append(user_id)
        save_json(BLACKLIST_FILE, blacklist)
    await ctx.send(f"☂️ Пользователь {user_id} ликвидирован")

@bot.command(name="амнистия")
async def amnesty(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    
    if user_id in blacklist:
        blacklist.remove(user_id)
        save_json(BLACKLIST_FILE, blacklist)
    await ctx.send(f"☂️ Пользователь {user_id} амнистирован")

@bot.command(name="черныйсписок")
async def show_blacklist(ctx):
    if not is_admin(ctx.author.id):
        return
    
    if not blacklist:
        await ctx.send("☂️ Чёрный список пуст")
        return
    
    await ctx.send(f"☂️ **Чёрный список:**\n" + "\n".join([f"🚫 ID: {uid}" for uid in blacklist]))

# ==================== ТЕРМИНАЛ ====================
async def show_terminal(user):
    is_adm = is_admin(user.id)
    
    embed = discord.Embed(
        title="☂️ **МОГ-ЗОНТ | ТЕРМИНАЛ**",
        color=discord.Color.dark_red()
    )
    
    embed.add_field(
        name="📌 КОМАНДЫ",
        value="`!старт` — Активация\n"
              "`!связь` — Проверка связи\n"
              "`!терминал` — Этот список\n"
              "`!связаться <ID> <текст>` — Анонимное сообщение\n"
              "`!канал <ID> <текст>` — Отправить в канал\n"
              "`!слежка <ID>` — Начать слежку\n"
              "`!снятьслежку <ID>` — Остановить слежку\n"
              "`!списокцелей` — Список целей",
        inline=False
    )
    
    if is_adm:
        embed.add_field(
            name="⚠️ АДМИН",
            value="`!ликвидировать <ID>` — Блок\n"
                  "`!амнистия <ID>` — Разблок\n"
                  "`!черныйсписок` — Список блоков",
            inline=False
        )
    
    await user.send(embed=embed)

# ==================== ЗАПУСК ====================
async def main():
    while True:
        try:
            async with bot:
                await bot.start(TOKEN)
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())