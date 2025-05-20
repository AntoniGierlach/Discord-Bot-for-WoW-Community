import discord
from discord.ext import commands
from discord import app_commands, Embed
from datetime import datetime, timezone
from collections import defaultdict

class YappingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_counts = defaultdict(lambda: defaultdict(int))
        self.user_message_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
        self.YAPPING_LEVELS = {
            "Negative yapping": 0,
            "Low": 100,
            "Moderate": 250,
            "High": 350,
            "Very high": 500,
            "Extreme": 750,
            "CATASTROPHIC": 1000,
        }

    async def initialize_message_counts(self):
        today = datetime.now(timezone.utc).date()

        for guild in self.bot.guilds:
            guild_id = guild.id
            self.message_counts[guild_id][today] = 0
            self.user_message_counts[guild_id].clear()

            for channel in guild.text_channels:
                try:
                    after_date = datetime.combine(today, datetime.min.time(), timezone.utc)
                    async for message in channel.history(limit=None, after=after_date):
                        await self.increment_message_count(guild_id, message.author.id)
                except discord.Forbidden:
                    print(f"⚠️ Brak dostępu do kanału: {channel.name}")
                except Exception as e:
                    print(f"⚠️ Błąd w kanale {channel.name}: {e}")

    def determine_yapping_level(self, message_count):
        for level, threshold in reversed(self.YAPPING_LEVELS.items()):
            if message_count >= threshold:
                return level
        return "low"

    async def increment_message_count(self, guild_id, user_id):
        today = datetime.now(timezone.utc).date()
        
        if today not in self.message_counts[guild_id]:
            self.message_counts[guild_id][today] = 0
        if today not in self.user_message_counts[guild_id][user_id]:
            self.user_message_counts[guild_id][user_id][today] = 0

        self.message_counts[guild_id][today] += 1
        self.user_message_counts[guild_id][user_id][today] += 1

    @app_commands.command(name="yapping", description="Sprawdź poziom yappingu na serwerze.")
    async def yapping_level(self, interaction: discord.Interaction):
        try:
            today = datetime.now(timezone.utc).date()
            guild_id = interaction.guild.id
            
            count = self.message_counts.get(guild_id, {}).get(today, 0)
            level = self.determine_yapping_level(count)

            embed = Embed(
                title=f"Yapping 🔻 {interaction.guild.name}",
                description=f"Poziom yappingu dzisiaj to:\n**{level}** - **{count}** wiadomości <a:Yapping:1341073527134093423>",
                color=discord.Color.purple()
            )

            embed.set_thumbnail(
                url=interaction.guild.icon.url if interaction.guild.icon 
                else "https://ia800305.us.archive.org/31/items/discordprofilepictures/discordred.png"
            )

            embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_embed = Embed(
                title="Błąd",
                description="Wystąpił błąd podczas sprawdzania statystyk yappingu.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            print(f"Błąd w yapping_level: {e}")

    @app_commands.command(name="yapping_user", description="Sprawdź liczbę wiadomości wysłanych dzisiaj przez użytkownika.")
    @app_commands.describe(member="Wybierz użytkownika")
    async def yapping_user(self, interaction: discord.Interaction, member: discord.Member):
        today = datetime.now(timezone.utc).date()
        guild_id = interaction.guild.id
        user_id = member.id
        
        count = self.user_message_counts.get(guild_id, {}).get(user_id, {}).get(today, 0)

        embed = Embed(
            title=f"Yapping 🔻 {member.display_name}",
            description=f"{member.display_name} napisał dzisiaj **{count}** wiadomości <a:Chatting2:1341072323318386768>",
            color=discord.Color.red()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    yapping_cog = YappingCommands(bot)
    await bot.add_cog(yapping_cog)
    await yapping_cog.initialize_message_counts()  # Inicjalizacja historii wiadomości