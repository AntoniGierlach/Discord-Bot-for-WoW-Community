import discord
from discord.ext import commands
from discord import app_commands

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="muteall", description="Wycisza wszystkich użytkowników na kanale głosowym.")
    async def muteall(self, interaction: discord.Interaction):
        if 1212783011305889822 not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Nie jesteś na kanale głosowym.", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        for member in channel.members:
            if 1212783011305889822 not in [role.id for role in member.roles]:
                await member.edit(mute=True)
        await interaction.response.send_message("✅ Wyciszono wszystkich użytkowników na kanale.")

    @app_commands.command(name="unmuteall", description="Wyłącza wyciszenie wszystkim użytkownikom na kanale głosowym.")
    async def unmuteall(self, interaction: discord.Interaction):
        try:
            if 1212783011305889822 not in [role.id for role in interaction.user.roles]:
                await interaction.response.send_message("❌ Nie masz uprawnień do użycia tej komendy.", ephemeral=True)
                return

            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message("❌ Nie jesteś na kanale głosowym.", ephemeral=True)
                return

            await interaction.response.defer()
            channel = interaction.user.voice.channel
            for member in channel.members:
                await member.edit(mute=False)

            await interaction.followup.send("✅ Wyciszenie zostało wyłączone dla wszystkich użytkowników na kanale.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Bot nie ma uprawnień do zarządzania użytkownikami na tym kanale.")
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił błąd: {e}")

async def setup(bot):
    await bot.add_cog(ModerationCommands(bot))