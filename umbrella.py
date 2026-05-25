import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os

TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = 991057181677850694
LOG_CHANNEL_ID = 1505668325236019343  # ID канала для логов СЛЕЖКИ (не для чата)

# ВСЁ В ПАМЯТИ
blacklist = []
chat_sessions = {}
watched_users = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def is_blacklisted(user_id):
    return user_id in blacklist

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_watched(user_id):
    return user_id in watched_users

async def log_to_channel(text):
    """Логи СЛЕЖКИ (не анонимного чата)"""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

async def log_to_admin(embed):
    """Отправляет embed админу в ЛС"""
    try:
        admin = await bot.fetch_user(ADMIN_ID)
        await admin.send(embed=embed)
    except:
        pass

def make_embed(title, description, color=0x8B0000):
    embed = discord.Embed(
        title=f"☂️ **{title}**",
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Umbrella Corporation | МОГ-Зонт")
    embed.set_thumbnail(url="https://i.pinimg.com/originals/23/d8/ec/23d8ec34996d8cb5749d40bc8322b464.jpg")
    return embed

@bot.event
async def on_ready():
    print(f"☂️ {bot.user} — МОГ-Зонт активирован")
    admin = await bot.fetch_user(ADMIN_ID)
    await admin.send(embed=make_embed(
        "СИСТЕМА АКТИВИРОВАНА",
        "Мобильная оперативная группа «Зонт» готова к работе.\n\n**Все сообщения агентов дублируются вам в ЛС.**\nЛоги слежки идут в указанный канал."
    ))

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Обработка ЛС
    if isinstance(message.channel, discord.DMChannel):
        user_id = message.author.id
        
        if is_blacklisted(user_id):
            await message.author.send(embed=make_embed(
                "ДОСТУП ЗАБЛОКИРОВАН",
                "Вы были ликвидированы из системы.",
                0x8B0000
            ))
            return
        
        if message.content == "!старт":
            await message.author.send(embed=make_embed(
                "ДОБРО ПОЖАЛОВАТЬ",
                f"**{message.author.name}**\nВаш ID: `{user_id}`\n\nВведите `!терминал`",
                0x8B0000
            ))
            await log_to_admin(make_embed(
                "НОВЫЙ АГЕНТ",
                f"{message.author.name} (ID: {user_id}) активировал систему.",
                0x8B0000
            ))
            return
        
        if message.content == "!терминал":
            await show_terminal(message.author)
            return
        
        if message.content == "!связь":
            await message.author.send(embed=make_embed(
                "СТАТУС",
                "🟢 ОНЛАЙН",
                0x00FF00
            ))
            return
        
        # !связаться
        if message.content.startswith("!связаться"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.author.send(embed=make_embed("ОШИБКА", "!связаться <ID> <текст>", 0x8B0000))
                return
            
            try:
                target_id = int(parts[1])
                text = parts[2]
                target = await bot.fetch_user(target_id)
                
                await target.send(embed=make_embed(
                    "АНОНИМНОЕ СООБЩЕНИЕ",
                    f"{text}",
                    0x8B0000
                ))
                
                chat_sessions[target.id] = user_id
                
                await message.author.send(embed=make_embed(
                    "ОТПРАВЛЕНО",
                    f"Пользователю {target.name}",
                    0x00FF00
                ))
                
                # ТОЛЬКО АДМИНУ, НЕ В КАНАЛ
                await log_to_admin(make_embed(
                    "ДОСЬЕ | ПЕРЕХВАТ",
                    f"**Агент:** {message.author.name} (ID: {user_id})\n"
                    f"**Цель:** {target.name} (ID: {target_id})\n"
                    f"**Текст:**\n```{text}```",
                    0x8B0000
                ))
                
            except:
                await message.author.send(embed=make_embed("ОШИБКА", "Пользователь не найден", 0x8B0000))
            return
        
        # !канал
        if message.content.startswith("!канал"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                return
            
            try:
                channel_id = int(parts[1])
                text = parts[2]
                channel = bot.get_channel(channel_id)
                
                if channel:
                    await channel.send(embed=make_embed("СООБЩЕНИЕ", text, 0x8B0000))
                    await message.author.send(embed=make_embed("ОТПРАВЛЕНО", f"В {channel.name}", 0x00FF00))
                    
                    await log_to_admin(make_embed(
                        "ОТПРАВКА В КАНАЛ",
                        f"**Агент:** {message.author.name}\n**Канал:** {channel.name}\n**Текст:**\n```{text}```",
                        0x8B0000
                    ))
            except:
                pass
            return
        
        # Ответ в анонимном чате
        if user_id in chat_sessions:
            partner_id = chat_sessions[user_id]
            try:
                partner = await bot.fetch_user(partner_id)
                await partner.send(embed=make_embed("ОТВЕТ", message.content, 0x8B0000))
                
                # ТОЛЬКО АДМИНУ, НЕ В КАНАЛ
                await log_to_admin(make_embed(
                    "ДОСЬЕ | ОТВЕТ",
                    f"**Цель:** {message.author.name} (ID: {user_id})\n"
                    f"**Агент:** {partner.name}\n"
                    f"**Текст:**\n```{message.content}```",
                    0x8B0000
                ))
            except:
                pass
            return
        
        await message.author.send(embed=make_embed("НЕИЗВЕСТНАЯ КОМАНДА", "!терминал", 0x8B0000))
        return
    
    # ===== СЕРВЕРНАЯ СЛЕЖКА (это идёт в канал) =====
    if message.guild and is_watched(message.author.id):
        await log_to_channel(
            f"☂️ **СООБЩЕНИЕ ОТ ЦЕЛИ**\n"
            f"👤 {message.author.name}\n"
            f"📝 {message.content[:500]}"
        )
        
        await log_to_admin(make_embed(
            "СЛЕЖКА | СООБЩЕНИЕ",
            f"**Цель:** {message.author.name}\n**Текст:**\n```{message.content[:500]}```",
            0x8B0000
        ))
    
    await bot.process_commands(message)

# ===== ОСТАЛЬНЫЕ СОБЫТИЯ СЛЕЖКИ (в канал и админу) =====
@bot.event
async def on_presence_update(before, after):
    if after.guild and is_watched(after.id) and before.status != after.status:
        await log_to_channel(f"☂️ **СТАТУС** {after.name}: {before.status} → {after.status}")
        await log_to_admin(make_embed("СЛЕЖКА | СТАТУС", f"{after.name}: {before.status} → {after.status}", 0x8B0000))

@bot.event
async def on_voice_state_update(member, before, after):
    if is_watched(member.id) and before.channel != after.channel:
        if after.channel:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} → {after.channel.name}")
        else:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} вышел из {before.channel.name}")

@bot.event
async def on_member_join(member):
    if is_watched(member.id):
        await log_to_channel(f"☂️ **ВХОД** {member.name} на {member.guild.name}")

# ===== КОМАНДЫ =====
@bot.command(name="слежка")
async def start_watch(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    try:
        user = await bot.fetch_user(user_id)
        watched_users[user_id] = user.name
        await ctx.send(embed=make_embed("СЛЕЖКА АКТИВИРОВАНА", f"Цель: {user.name}", 0x8B0000))
        await log_to_channel(f"☂️ Слежка: {user.name} (инициатор: {ctx.author.name})")
    except:
        await ctx.send(embed=make_embed("ОШИБКА", "Не найден", 0x8B0000))

@bot.command(name="снятьслежку")
async def stop_watch(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    if user_id in watched_users:
        name = watched_users[user_id]
        del watched_users[user_id]
        await ctx.send(embed=make_embed("СЛЕЖКА ОСТАНОВЛЕНА", f"{name}", 0x8B0000))

@bot.command(name="списокцелей")
async def list_watch(ctx):
    if is_blacklisted(ctx.author.id):
        return
    if not watched_users:
        await ctx.send(embed=make_embed("СПИСОК ЦЕЛЕЙ", "Нет", 0x8B0000))
        return
    targets = "\n".join([f"👤 {name} (ID: {uid})" for uid, name in watched_users.items()])
    await ctx.send(embed=make_embed("ЦЕЛИ", targets, 0x8B0000))

@bot.command(name="ликвидировать")
async def block_user(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    if user_id not in blacklist:
        blacklist.append(user_id)
    await ctx.send(embed=make_embed("ЛИКВИДАЦИЯ", f"{user_id} заблокирован", 0x8B0000))

@bot.command(name="амнистия")
async def unblock_user(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    if user_id in blacklist:
        blacklist.remove(user_id)
    await ctx.send(embed=make_embed("АМНИСТИЯ", f"{user_id} разблокирован", 0x00FF00))

@bot.command(name="черныйсписок")
async def list_blacklist(ctx):
    if not is_admin(ctx.author.id):
        return
    if not blacklist:
        await ctx.send(embed=make_embed("ЧЁРНЫЙ СПИСОК", "Пуст", 0x8B0000))
        return
    await ctx.send(embed=make_embed("ЧЁРНЫЙ СПИСОК", "\n".join([f"🚫 ID: {uid}" for uid in blacklist]), 0x8B0000))

async def show_terminal(user):
    is_adm = is_admin(user.id)
    text = (
        "`!связаться <ID> <текст>` — Анонимное сообщение\n"
        "`!канал <ID> <текст>` — Отправить в канал\n"
        "`!слежка <ID>` — Начать слежку\n"
        "`!снятьслежку <ID>` — Остановить слежку\n"
        "`!списокцелей` — Список целей\n"
        "`!связь` — Проверка связи\n"
        "`!терминал` — Этот список"
    )
    if is_adm:
        text += "\n\n**АДМИН:**\n`!ликвидировать <ID>`\n`!амнистия <ID>`\n`!черныйсписок`"
    await user.send(embed=make_embed("ТЕРМИНАЛ", text, 0x8B0000))

async def main():
    while True:
        try:
            async with bot:
                await bot.start(TOKEN)
        except:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
