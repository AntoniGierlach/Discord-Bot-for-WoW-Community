import discord
import random
from discord.ext import commands
from discord import app_commands, Embed

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fortunes = [
            "Dziś spotka Cię miła niespodzianka",
            "Uważaj na nieoczekiwane wydarzenia",
            "Szczęście się do Ciebie uśmiecha",
            "To będzie Twój szczęśliwy dzień",
            "Może warto wziąć dziś dzień wolny?"
        ]
        self.compliments = [
            "Masz niesamowite poczucie humoru!",
            "Twoja energia jest zaraźliwa!",
            "Jesteś mistrzem w tym, co robisz!",
            "Ludzie lubią przebywać w Twoim towarzystwie!",
            "Masz talent do rozśmieszania innych!"
        ]

    @app_commands.command(name="fortune", description="Get a random fortune prediction")
    async def fortune(self, interaction: discord.Interaction):
        """Get a random fortune cookie message"""
        embed = Embed(
            title="🔮 Fortune Cookie",
            description=random.choice(self.fortunes),
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="compliment", description="Give someone a nice compliment")
    @app_commands.describe(user="User to compliment")
    async def compliment(self, interaction: discord.Interaction, user: discord.Member):
        """Send a random compliment to a user"""
        embed = Embed(
            title=f"💖 For {user.display_name}",
            description=random.choice(self.compliments),
            color=discord.Color.pink()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hype", description="Check your hype level")
    @app_commands.describe(level="Your hype level (0-100)")
    async def hype(self, interaction: discord.Interaction, level: app_commands.Range[int, 0, 100]):
        """Measure your hype level with a fun visual"""
        user = interaction.user
        
        embed = Embed(
            title=f"🎉 {user.display_name}'s Hype Meter",
            description=f"Your hype level: **{level}%**",
            color=discord.Color.green()
        )
        
        # Visual hype meter
        meter = "🟩" * (level // 10)
        meter += "⬛" * (10 - (level // 10))
        
        if level < 20:
            embed.add_field(name="Status", value="Could use more energy! " + meter, inline=False)
        elif 20 <= level < 50:
            embed.add_field(name="Status", value="Getting warmed up! " + meter, inline=False)
        elif 50 <= level < 80:
            embed.add_field(name="Status", value="Now we're talking! " + meter, inline=False)
        else:
            embed.add_field(name="Status", value="MAXIMUM HYPE! " + meter, inline=False)

        embed.set_thumbnail(url=user.avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your yes/no question")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        """Classic magic 8-ball command"""
        responses = [
            "It is certain", "It is decidedly so", "Without a doubt",
            "Yes definitely", "You may rely on it", "As I see it, yes",
            "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy try again", "Ask again later",
            "Better not tell you now", "Cannot predict now",
            "Concentrate and ask again", "Don't count on it",
            "My reply is no", "My sources say no", "Outlook not so good",
            "Very doubtful"
        ]
        
        embed = Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {random.choice(responses)}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FunCommands(bot))
