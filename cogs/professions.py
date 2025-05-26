import asyncio
import datetime
import discord
import json
import os
from discord.ext import commands, tasks
from discord import app_commands, ui

PROFESJE_CHANNEL_ID = 1375441476154298458
DATA_FILE = "data/profesje.json"
PROFESJE = {
    "Blacksmithing": "<:bs:1375428094864654409>",
    "Enchanting": "<:ench:1375428108823560202>",
    "Engineering": "<:eng:1375428121800474715>",
    "Inscription": "<:insc:1375428132454006784>",
    "Jewelcrafting": "<:jc:1375428142222545058>",
    "Leatherworking": "<:lw:1375428150355431596>",
    "Tailoring": "<:tailo:1375428159012339712>"
}


class ProfesjeSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.load_data()
        self.cleanup_task.start()

    def load_data(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                for prof in PROFESJE:
                    if prof not in data.get('crafters', {}):
                        data['crafters'][prof] = []
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'message_id': None,
                'crafters': {prof: [] for prof in PROFESJE}
            }

    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=4)

    @tasks.loop(hours=1)
    async def cleanup_task(self):
        await self.cleanup_old_messages()

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    async def cleanup_old_messages(self):
        channel = self.bot.get_channel(PROFESJE_CHANNEL_ID)
        if not channel:
            return

        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            cutoff = now - datetime.timedelta(hours=24)

            async for message in channel.history(limit=None):
                if message.id == self.data['message_id']:
                    continue

                if message.created_at < cutoff:
                    try:
                        await message.delete()
                        await asyncio.sleep(1)
                    except discord.NotFound:
                        pass
                    except discord.HTTPException as e:
                        print(f"Błąd podczas usuwania wiadomości: {e}")
        except Exception as e:
            print(f"Błąd podczas czyszczenia wiadomości: {e}")

    async def update_profesje_embed(self, channel):
        embed = discord.Embed(
            title="🧵 Solemnity Profesje ⚒️",
            description=
            "🔹 Nie ma kto zmajstrować itemka? - Pisz tu! 💬\n"
            "🔹 Daj znać czego potrzebujesz i ile dajesz napiwku 🤑\n"
            "🔹 Poniżej znajdziesz listę crafterów do kontaktu 😍\n\n"
            "**Crafterzy** ",

            color=discord.Color.dark_gold()
        )

        for prof, emoji in PROFESJE.items():
            crafters = self.data['crafters'].get(prof, [])
            crafters_list = "\n".join([f"<@{cid}>" for cid in crafters]) if crafters else "-# Brak crafterów"
            embed.add_field(
                name=f"{emoji} {prof}",
                value=crafters_list,
                inline=True
            )

        if channel.guild.icon:
            embed.set_thumbnail(url=channel.guild.icon.url)

        embed.set_footer(text="Wybierz profesję z menu poniżej aby zostać dodanym/usuniętym")

        view = discord.ui.View(timeout=None)
        view.add_item(ProfesjeSelectMenu())

        if self.data['message_id']:
            try:
                message = await channel.fetch_message(self.data['message_id'])
                await message.edit(embed=embed, view=view)
                return
            except discord.NotFound:
                pass

        embed.set_footer(text=f"Wybierz profesję z menu poniżej aby zostać dodanym/usuniętym")
        message = await channel.send(embed=embed, view=view)
        self.data['message_id'] = message.id
        self.save_data()

    @commands.Cog.listener()
    async def on_ready(self):
        print("System profesji gotowy!")
        channel = self.bot.get_channel(PROFESJE_CHANNEL_ID)
        if channel:
            await self.update_profesje_embed(channel)

    @app_commands.command(name="update_profesje", description="Aktualizuje embeda z profesjami")
    async def update_profesje(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.update_profesje_embed(interaction.channel)
        await interaction.followup.send("✅ Embed z profesjami został zaktualizowany!", ephemeral=True)


class ProfesjeSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=prof,
                emoji=emoji,
                description=f"Zapisz się do {prof}"
            ) for prof, emoji in PROFESJE.items()
        ]

        super().__init__(
            placeholder="Wybierz profesję...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="profesje_select"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_prof = self.values[0]
        user_id = interaction.user.id
        cog = interaction.client.get_cog("ProfesjeSystem")

        if user_id in cog.data['crafters'][selected_prof]:
            cog.data['crafters'][selected_prof].remove(user_id)
            action = "usunięty"
        else:
            cog.data['crafters'][selected_prof].append(user_id)
            action = "dodany"

        channel = interaction.client.get_channel(PROFESJE_CHANNEL_ID)
        await cog.update_profesje_embed(channel)
        cog.save_data()

        await interaction.response.send_message(
            f"✅ Zostałeś {action} jako {PROFESJE[selected_prof]} {selected_prof}!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(ProfesjeSystem(bot))