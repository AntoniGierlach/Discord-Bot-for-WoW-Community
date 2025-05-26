import discord
import requests
import random
from discord.ext import commands
from cogs.wow import WowCommands
from cogs.fun import FunCommands
from cogs.moderation import ModerationCommands
from cogs.yapping import YappingCommands
from cogs.professions import ProfesjeSystem
from cogs.absence import NieobecnosciSystem
from config import TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_responses():
    try:
        with open('data/responses.txt', 'r', encoding='utf-8') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        print("Plik 'responses.txt' nie istnieje. Utwórz plik z odpowiedziami.")
        return []


responses = load_responses()


async def load_cogs():
    await bot.add_cog(YappingCommands(bot))
    await bot.add_cog(WowCommands(bot))
    await bot.add_cog(FunCommands(bot))
    await bot.add_cog(ModerationCommands(bot))
    await bot.add_cog(ProfesjeSystem(bot))
    await bot.add_cog(NieobecnosciSystem(bot))


@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} jest online!")
    await load_cogs()

    yapping_cog = bot.get_cog("YappingCommands")
    if yapping_cog:
        await yapping_cog.initialize_message_counts()

    activity = discord.Streaming(name="via halori__", url="https://www.twitch.tv/halori__")
    await bot.change_presence(activity=activity)

    try:
        synced = await bot.tree.sync()
        print(f"✅ Zsynchronizowano {len(synced)} globalnych komend.")
    except Exception as e:
        print(f"❌ Błąd synchronizacji komend: {e}")


def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Wiadomość wysłana na Telegram: {message}")
        else:
            print(f"❌ Błąd podczas wysyłania wiadomości na Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Błąd połączenia z Telegram API: {e}")


@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None:
        return

    yapping_cog = bot.get_cog("YappingCommands")
    if yapping_cog:
        await yapping_cog.increment_message_count(message.guild.id, message.author.id)

    if str(bot.user.id) in message.content and responses:
        await message.reply(random.choice(responses))

    if message.reference:
        try:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message.author == bot.user and responses:
                await message.reply(random.choice(responses))
        except Exception as e:
            print(f"Błąd podczas pobierania wiadomości: {e}")

    for attachment in message.attachments:
        if attachment.filename.endswith('.mp4'):
            target_channel_id = 1233783179370823700

            if message.channel.id != target_channel_id:
                target_channel = bot.get_channel(target_channel_id)
                if target_channel:
                    try:
                        await message.forward(target_channel)
                        print(f"✅ Przekazano wiadomość z plikiem .mp4 na kanał {target_channel.name}.")
                    except discord.HTTPException as e:
                        print(f"❌ Błąd podczas przekazywania wiadomości: {e}")

    if message.channel.id == 1212808961061949542:
        send_telegram_message(f"{message.author.display_name} napisał na Discordzie:\n{message.content}")

    await bot.process_commands(message)

bot.run(TOKEN)