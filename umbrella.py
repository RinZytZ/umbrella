import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os

TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = 991057181677850694
LOG_CHANNEL_ID = 1505668325236019343  # ID канала для логов (укажите свой)

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
    """Создаёт красивое сообщение в стиле Umbrella"""
    embed = discord.Embed(
        title=f"☂️ **{title}**",
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Umbrella Corporation | МОГ-Зонт")
    embed.set_thumbnail(url="https://i.imgur.com/8xRnZkM.png")
    return embed

@bot.event
async def on_ready():
    print(f"☂️ {bot.user} — МОГ-Зонт активирован")
    admin = await bot.fetch_user(ADMIN_ID)
    await admin.send(embed=make_embed(
        "СИСТЕМА АКТИВИРОВАНА",
        "Мобильная оперативная группа «Зонт» готова к работе.\nВсе системы в норме.\n\n**Все сообщения агентов будут дублироваться вам.**"
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
                "Вы были ликвидированы из системы. Обратитесь к администратору.",
                0x8B0000
            ))
            return
        
        # !старт
        if message.content == "!старт":
            await message.author.send(embed=make_embed(
                "ДОБРО ПОЖАЛОВАТЬ",
                f"**Оперативник {message.author.name}**\n"
                f"Ваш ID: `{user_id}`\n\n"
                "Введите `!терминал` для доступа к командам.",
                0x8B0000
            ))
            
            # Дублируем админу
            await log_to_admin(make_embed(
                "НОВЫЙ АГЕНТ",
                f"**Имя:** {message.author.name}\n**ID:** {user_id}\nАктивировал систему.",
                0x8B0000
            ))
            return
        
        # !терминал
        if message.content == "!терминал":
            await show_terminal(message.author)
            return
        
        # !связь
        if message.content == "!связь":
            await message.author.send(embed=make_embed(
                "СТАТУС СИСТЕМЫ",
                "🟢 **ОНЛАЙН**\nСвязь с сервером установлена.",
                0x00FF00
            ))
            return
        
        # !связаться <ID> <текст>
        if message.content.startswith("!связаться"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                await message.author.send(embed=make_embed(
                    "ОШИБКА",
                    "Использование: `!связаться <ID> <текст>`",
                    0x8B0000
                ))
                return
            
            try:
                target_id = int(parts[1])
                text = parts[2]
                target = await bot.fetch_user(target_id)
                
                await target.send(embed=make_embed(
                    "АНОНИМНОЕ СООБЩЕНИЕ",
                    f"Вам пишет неизвестный оперативник:\n\n{text}",
                    0x8B0000
                ))
                
                chat_sessions[target.id] = user_id
                
                await message.author.send(embed=make_embed(
                    "ОТПРАВЛЕНО",
                    f"Сообщение доставлено пользователю `{target.name}`",
                    0x00FF00
                ))
                
                await log_to_channel(f"☂️ Анонимный чат: {message.author.name} → {target.name}")
                
                # Дублируем админу
                await log_to_admin(make_embed(
                    "ДОСЬЕ | ПЕРЕХВАТ СООБЩЕНИЯ",
                    f"**Агент:** {message.author.name} (ID: {user_id})\n"
                    f"**Цель:** {target.name} (ID: {target_id})\n"
                    f"**Текст:**\n```{text}```",
                    0x8B0000
                ))
                
            except Exception as e:
                await message.author.send(embed=make_embed(
                    "ОШИБКА",
                    f"Пользователь не найден: {e}",
                    0x8B0000
                ))
            return
        
        # !канал <ID> <текст>
        if message.content.startswith("!канал"):
            parts = message.content.split(maxsplit=2)
            if len(parts) < 3:
                return
            
            try:
                channel_id = int(parts[1])
                text = parts[2]
                channel = bot.get_channel(channel_id)
                
                if channel:
                    await channel.send(embed=make_embed(
                        "СООБЩЕНИЕ ОТ КОМАНДОВАНИЯ",
                        text,
                        0x8B0000
                    ))
                    await message.author.send(embed=make_embed(
                        "ОТПРАВЛЕНО",
                        f"Сообщение отправлено в канал `{channel.name}`",
                        0x00FF00
                    ))
                    
                    # Дублируем админу
                    await log_to_admin(make_embed(
                        "ОТПРАВКА В КАНАЛ",
                        f"**Агент:** {message.author.name} (ID: {user_id})\n"
                        f"**Канал:** {channel.name} (ID: {channel_id})\n"
                        f"**Текст:**\n```{text}```",
                        0x8B0000
                    ))
                else:
                    await message.author.send(embed=make_embed(
                        "ОШИБКА",
                        "Канал не найден",
                        0x8B0000
                    ))
            except:
                pass
            return
        
        # Ответ в анонимном чате (от цели агенту)
        if user_id in chat_sessions:
            partner_id = chat_sessions[user_id]
            try:
                partner = await bot.fetch_user(partner_id)
                await partner.send(embed=make_embed(
                    "ОТВЕТ В АНОНИМНОМ ЧАТЕ",
                    message.content,
                    0x8B0000
                ))
                await log_to_channel(f"☂️ Ответ в чате: {message.author.name} → {partner.name}")
                
                # Дублируем админу
                await log_to_admin(make_embed(
                    "ДОСЬЕ | ОТВЕТ ЦЕЛИ",
                    f"**Цель:** {message.author.name} (ID: {user_id})\n"
                    f"**Агент:** {partner.name} (ID: {partner_id})\n"
                    f"**Текст:**\n```{message.content}```",
                    0x8B0000
                ))
            except:
                pass
            return
        
        await message.author.send(embed=make_embed(
            "НЕИЗВЕСТНАЯ КОМАНДА",
            "Введите `!терминал` для списка команд",
            0x8B0000
        ))
        return
    
    # Серверная слежка
    if message.guild and is_watched(message.author.id):
        await log_to_channel(
            f"☂️ **СООБЩЕНИЕ ОТ ЦЕЛИ**\n"
            f"👤 {message.author.name}\n"
            f"📝 {message.content[:500]}"
        )
        
        # Дублируем админу
        await log_to_admin(make_embed(
            "СЛЕЖКА | СООБЩЕНИЕ",
            f"**Цель:** {message.author.name} (ID: {message.author.id})\n"
            f"**Канал:** #{message.channel.name}\n"
            f"**Текст:**\n```{message.content[:500]}```",
            0x8B0000
        ))
    
    await bot.process_commands(message)

# ===== СОБЫТИЯ СЛЕЖКИ =====
@bot.event
async def on_presence_update(before, after):
    if after.guild and is_watched(after.id) and before.status != after.status:
        await log_to_channel(f"☂️ **СМЕНА СТАТУСА** {after.name}: {before.status} → {after.status}")
        
        # Дублируем админу
        await log_to_admin(make_embed(
            "СЛЕЖКА | СТАТУС",
            f"**Цель:** {after.name} (ID: {after.id})\n"
            f"**Был:** {before.status}\n"
            f"**Стал:** {after.status}",
            0x8B0000
        ))

@bot.event
async def on_voice_state_update(member, before, after):
    if is_watched(member.id) and before.channel != after.channel:
        if after.channel:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} зашёл в {after.channel.name}")
            await log_to_admin(make_embed(
                "СЛЕЖКА | ГОЛОС",
                f"**Цель:** {member.name} (ID: {member.id})\n"
                f"**Действие:** Зашёл в голосовой канал\n"
                f"**Канал:** {after.channel.name}",
                0x8B0000
            ))
        else:
            await log_to_channel(f"☂️ **ГОЛОС** {member.name} вышел из {before.channel.name}")
            await log_to_admin(make_embed(
                "СЛЕЖКА | ГОЛОС",
                f"**Цель:** {member.name} (ID: {member.id})\n"
                f"**Действие:** Вышел из голосового канала\n"
                f"**Канал:** {before.channel.name}",
                0x8B0000
            ))

@bot.event
async def on_member_join(member):
    if is_watched(member.id):
        await log_to_channel(f"☂️ **ВХОД** {member.name} зашёл на сервер {member.guild.name}")
        await log_to_admin(make_embed(
            "СЛЕЖКА | ВХОД НА СЕРВЕР",
            f"**Цель:** {member.name} (ID: {member.id})\n"
            f"**Сервер:** {member.guild.name}",
            0x8B0000
        ))

# ===== КОМАНДЫ =====
@bot.command(name="слежка")
async def start_watch(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    
    try:
        user = await bot.fetch_user(user_id)
        watched_users[user_id] = user.name
        await ctx.send(embed=make_embed(
            "СЛЕЖКА АКТИВИРОВАНА",
            f"Цель: `{user.name}` (ID: {user_id})\nВсе действия будут отправлены в лог-канал.",
            0x8B0000
        ))
        await log_to_channel(f"☂️ Слежка начата: {user.name} (инициатор: {ctx.author.name})")
        await log_to_admin(make_embed(
            "СЛЕЖКА | НОВАЯ ЦЕЛЬ",
            f"**Инициатор:** {ctx.author.name} (ID: {ctx.author.id})\n"
            f"**Цель:** {user.name} (ID: {user_id})",
            0x8B0000
        ))
    except:
        await ctx.send(embed=make_embed("ОШИБКА", "Пользователь не найден", 0x8B0000))

@bot.command(name="снятьслежку")
async def stop_watch(ctx, user_id: int):
    if is_blacklisted(ctx.author.id):
        return
    
    if user_id in watched_users:
        name = watched_users[user_id]
        del watched_users[user_id]
        await ctx.send(embed=make_embed(
            "СЛЕЖКА ОСТАНОВЛЕНА",
            f"Цель `{name}` больше не отслеживается",
            0x8B0000
        ))
        await log_to_channel(f"☂️ Слежка остановлена: {name}")
        await log_to_admin(make_embed(
            "СЛЕЖКА | ОСТАНОВЛЕНА",
            f"**Инициатор:** {ctx.author.name} (ID: {ctx.author.id})\n"
            f"**Цель:** {name} (ID: {user_id})",
            0x8B0000
        ))
    else:
        await ctx.send(embed=make_embed("ОШИБКА", "Цель не найдена", 0x8B0000))

@bot.command(name="списокцелей")
async def list_watch(ctx):
    if is_blacklisted(ctx.author.id):
        return
    
    if not watched_users:
        await ctx.send(embed=make_embed("СПИСОК ЦЕЛЕЙ", "Нет активных целей", 0x8B0000))
        return
    
    targets = "\n".join([f"👤 `{name}` (ID: {uid})" for uid, name in watched_users.items()])
    await ctx.send(embed=make_embed("АКТИВНЫЕ ЦЕЛИ", targets, 0x8B0000))

@bot.command(name="ликвидировать")
async def block_user(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    
    if user_id not in blacklist:
        blacklist.append(user_id)
    await ctx.send(embed=make_embed(
        "ЛИКВИДАЦИЯ",
        f"Пользователь `{user_id}` ликвидирован. Доступ к системе заблокирован.",
        0x8B0000
    ))
    await log_to_channel(f"☂️ Ликвидирован: {user_id} (админ: {ctx.author.name})")
    await log_to_admin(make_embed(
        "АДМИН | ЛИКВИДАЦИЯ",
        f"**Администратор:** {ctx.author.name} (ID: {ctx.author.id})\n"
        f"**Заблокирован:** ID {user_id}",
        0x8B0000
    ))

@bot.command(name="амнистия")
async def unblock_user(ctx, user_id: int):
    if not is_admin(ctx.author.id):
        return
    
    if user_id in blacklist:
        blacklist.remove(user_id)
    await ctx.send(embed=make_embed(
        "АМНИСТИЯ",
        f"Пользователь `{user_id}` амнистирован. Доступ восстановлен.",
        0x00FF00
    ))
    await log_to_channel(f"☂️ Амнистирован: {user_id} (админ: {ctx.author.name})")
    await log_to_admin(make_embed(
        "АДМИН | АМНИСТИЯ",
        f"**Администратор:** {ctx.author.name} (ID: {ctx.author.id})\n"
        f"**Разблокирован:** ID {user_id}",
        0x00FF00
    ))

@bot.command(name="черныйсписок")
async def list_blacklist(ctx):
    if not is_admin(ctx.author.id):
        return
    
    if not blacklist:
        await ctx.send(embed=make_embed("ЧЁРНЫЙ СПИСОК", "Пуст", 0x8B0000))
        return
    
    await ctx.send(embed=make_embed(
        "ЧЁРНЫЙ СПИСОК",
        "\n".join([f"🚫 ID: `{uid}`" for uid in blacklist]),
        0x8B0000
    ))

async def show_terminal(user):
    is_adm = is_admin(user.id)
    
    commands_list = (
        "`!связаться <ID> <текст>` — Анонимное сообщение\n"
        "`!канал <ID_канала> <текст>` — Отправить в канал\n"
        "`!слежка <ID>` — Начать слежку\n"
        "`!снятьслежку <ID>` — Остановить слежку\n"
        "`!списокцелей` — Список целей\n"
        "`!связь` — Проверка связи\n"
        "`!терминал` — Этот список"
    )
    
    if is_adm:
        commands_list += "\n\n**АДМИНИСТРАТОРСКИЕ:**\n`!ликвидировать <ID>` — Блокировка\n`!амнистия <ID>` — Разблокировка\n`!черныйсписок` — Список заблокированных"
    
    await user.send(embed=make_embed("ТЕРМИНАЛ МОГ-ЗОНТ", commands_list, 0x8B0000))

# ===== ЗАПУСК =====
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
