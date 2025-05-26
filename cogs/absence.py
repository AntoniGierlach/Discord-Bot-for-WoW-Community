import asyncio
import discord
import json
import os
import datetime
from discord.ext import commands, tasks
from discord import app_commands, ui

ABSENCE_CHANNEL_ID = 1375491731989987370
ABSENCE_FILE = "data/nieobecnosci.json"


class NieobecnosciSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.absences = self.load_data()
        self.cleanup_task.start()

    def load_data(self):
        os.makedirs(os.path.dirname(ABSENCE_FILE), exist_ok=True)
        try:
            with open(ABSENCE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'message_id': None,
                'absences': []
            }

    def save_data(self):
        with open(ABSENCE_FILE, 'w') as f:
            json.dump(self.absences, f, indent=4)

    def is_valid_date(self, day, month, year=None):
        """Sprawdza czy data jest poprawna"""
        try:
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            if month in [4, 6, 9, 11] and day > 30:
                return False
            if month == 2:
                if day > 28:
                    return False

            return True
        except (TypeError, ValueError):
            return False

    def format_date_with_weekday(self, date_str):
        """Formatuje datę YYYY-MM-DD na DD.MM | DzieńTygodnia z walidacją"""
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            weekday = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"][
                date_obj.weekday()]
            return f"{date_obj.day:02d}.{date_obj.month:02d} | {weekday}"
        except ValueError:
            print(f"[BŁĄD] Nieprawidłowa data do formatowania: {date_str}")
            return "Nieprawidłowa data"

    @tasks.loop(hours=1)
    async def cleanup_task(self):
        await self.check_expired_absences()
        await self.cleanup_old_messages()

    @cleanup_task.before_loop
    async def before_cleanup(self):
       await self.bot.wait_until_ready()

    async def check_expired_absences(self):
        changed = False
        new_absences = []
        removed_count = 0

        for absence in self.absences['absences']:
            try:
                if not self.is_absence_expired(absence['end_date']):
                    new_absences.append(absence)
                else:
                    removed_count += 1
                    changed = True
            except Exception as e:
                print(f"Błąd podczas sprawdzania nieobecności {absence}: {e}")
                removed_count += 1
                changed = True

        self.absences['absences'] = new_absences

        for abs in self.absences['absences']:
            print(f"User: {abs['user_id']}, Typ: {abs['type']}, Data: {abs['end_date']}")

        if changed or removed_count > 0:
            channel = self.bot.get_channel(ABSENCE_CHANNEL_ID)
            if channel:
                try:
                    await self.update_absence_embed(channel)
                    self.save_data()
                except Exception as e:
                    print(f"Błąd podczas aktualizacji embeda: {e}")

    def is_absence_expired(self, end_date_str):
        try:
            end_date_str = end_date_str.strip()
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
            return datetime.date.today() > end_date
        except ValueError as e:
            print(f"[BŁĄD DATY] Nie można przetworzyć daty '{end_date_str}': {e} - wpis zostanie usunięty")
            return True

    async def cleanup_old_messages(self):
        channel = self.bot.get_channel(ABSENCE_CHANNEL_ID)
        if not channel:
            return

        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            cutoff = now - datetime.timedelta(hours=24)

            async for message in channel.history(limit=None):
                if (message.id == self.absences['message_id'] or
                        (message.interaction_metadata is not None and message.created_at > now - datetime.timedelta(
                            hours=24))):
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

    async def update_absence_embed(self, channel):
        """Aktualizuje embed z listą nieobecności z pełną walidacją danych"""
        embed = discord.Embed(
            title="📅 Solemnity Nieobecności ⌛",
            description=(
                "🔹 RL nie odpuszcza? Zgłoś nieobecność! 📝\n"
                "🔹 Raidy bez Ciebie to nie to samo, ale damy radę! 😢\n"
                "🔹 Nie musisz się tłumaczyć, ale info = gold 💰"
            ),
            color=discord.Color.orange()
        )

        valid_absences = []
        invalid_count = 0

        for absence in self.absences['absences']:
            try:
                start_date = absence['start_date']
                end_date = absence['end_date']

                datetime.datetime.strptime(start_date, "%Y-%m-%d")
                datetime.datetime.strptime(end_date, "%Y-%m-%d")

                start_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                end_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

                if end_obj < start_obj:
                    invalid_count += 1
                    continue

                valid_absences.append(absence)

            except (ValueError, KeyError) as e:
                invalid_count += 1
                print(f"[USUWAM] Nieprawidłowy wpis nieobecności: {absence} | Błąd: {e}")
                continue

        if invalid_count > 0:
            print(f"Znaleziono {invalid_count} nieprawidłowych wpisów nieobecności")

        sorted_absences = sorted(valid_absences, key=lambda x: x['start_date'])
        daily = []
        period = []
        late = []

        for absence in sorted_absences:
            try:
                user = f"<@{absence['user_id']}>"
                start_date = self.format_date_with_weekday(absence['start_date'])

                if absence['type'] == 'daily':
                    daily.append(f"{user} - {start_date}")
                elif absence['type'] == 'period':
                    end_date = self.format_date_with_weekday(absence['end_date'])
                    period.append(f"{user} - {start_date} do {end_date}")
                elif absence['type'] == 'late':
                    late.append(f"{user} - {start_date} (spóźnienie)")

            except Exception as e:
                print(f"Błąd podczas przetwarzania wpisu {absence}: {e}")

        try:
            if daily:
                embed.add_field(name="🗓️ Jednodniowe nieobecności", value="\n".join(daily) or "-", inline=False)
            if period:
                embed.add_field(name="🏖️ Dłuższe nieobecności", value="\n".join(period) or "-", inline=False)
            if late:
                embed.add_field(name="⏰ Spóźnienia", value="\n".join(late) or "-", inline=False)

            if not daily and not period and not late:
                embed.add_field(
                    name="Brak nieobecności <:noway:1212775686276915270>",
                    value="-# Wszyscy są dostępni!",
                    inline=False
                )

            if channel.guild.icon:
                embed.set_thumbnail(url=channel.guild.icon.url)

            embed.set_footer(text="Zgłoś swoją nieobecność korzystając z menu poniżej")

        except Exception as e:
            print(f"Błąd podczas budowania embeda: {e}")
            embed.add_field(
                name="❌ Błąd systemu",
                value="Wystąpił problem z wyświetleniem listy nieobecności",
                inline=False
            )

        view = discord.ui.View(timeout=None)
        try:
            view.add_item(NieobecnosciSelectMenu())
        except Exception as e:
            print(f"Błąd podczas tworzenia menu: {e}")

        try:
            if self.absences.get('message_id'):
                try:
                    message = await channel.fetch_message(self.absences['message_id'])
                    await message.edit(embed=embed, view=view)
                    return
                except discord.NotFound:
                    print("Nie znaleziono wiadomości embeda, wysyłam nową...")
                except discord.HTTPException as e:
                    print(f"Błąd podczas edycji wiadomości: {e}")

            message = await channel.send(embed=embed, view=view)
            self.absences['message_id'] = message.id
            self.save_data()

        except Exception as e:
            print(f"Krytyczny błąd podczas aktualizacji embeda: {e}")
            try:
                await channel.send(
                    "⚠️ Nie udało się zaktualizować listy nieobecności. Proszę powiadomić administratora."
                )
            except:
                pass

    @commands.Cog.listener()
    async def on_ready(self):
        print("System nieobecności gotowy!")
        channel = self.bot.get_channel(ABSENCE_CHANNEL_ID)
        if channel:
            await self.update_absence_embed(channel)

    @app_commands.command(name="update_absences", description="Aktualizuje embeda z nieobecnościami")
    async def update_absences(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.update_absence_embed(interaction.channel)
        await interaction.followup.send("✅ Embed z nieobecnościami został zaktualizowany!", ephemeral=True)

    def cog_unload(self):
        self.cleanup_task.cancel()

class NieobecnosciSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Jednodniowa nieobecność",
                value="daily",
                emoji="🗓️",
                description="Zgłoś nieobecność na jeden dzień"
            ),
            discord.SelectOption(
                label="Dłuższa nieobecność",
                value="period",
                emoji="🏖️",
                description="Zgłoś nieobecność na okres czasu"
            ),
            discord.SelectOption(
                label="Spóźnienie",
                value="late",
                emoji="⏰",
                description="Zgłoś możliwe spóźnienie"
            ),
            discord.SelectOption(
                label="Wyczyść moje wpisy",
                value="clear",
                emoji="🧹",
                description="Usuń wszystkie moje zgłoszenia"
            )
        ]
        super().__init__(
            placeholder="Wybierz typ nieobecności...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="absence_select"
        )

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("NieobecnosciSystem")

        if self.values[0] == "clear":
            initial_count = len(cog.absences['absences'])
            cog.absences['absences'] = [
                abs for abs in cog.absences['absences']
                if abs['user_id'] != str(interaction.user.id)
            ]
            removed_count = initial_count - len(cog.absences['absences'])

            channel = interaction.client.get_channel(ABSENCE_CHANNEL_ID)
            await cog.update_absence_embed(channel)
            cog.save_data()

            await interaction.response.send_message(
                f"✅ Usunięto {removed_count} twoich wpisów!",
                ephemeral=True
            )
            return

        absence_type = self.values[0]
        modal = None

        if absence_type == "daily":
            modal = DailyAbsenceModal()
        elif absence_type == "period":
            modal = PeriodAbsenceModal()
        elif absence_type == "late":
            modal = LateAbsenceModal()

        if modal:
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("❌ Wystąpił błąd!", ephemeral=True)


class DailyAbsenceModal(ui.Modal, title="Zgłoś jednodniową nieobecność"):
    date = ui.TextInput(
        label="Data (DD.MM)",
        placeholder="np. 15.06",
        required=True,
        max_length=5,
        min_length=4
    )

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("NieobecnosciSystem")
        today = datetime.date.today()

        try:
            if '.' not in self.date.value or len(self.date.value.split('.')) != 2:
                raise ValueError("Użyj formatu DD.MM")

            day, month = map(int, self.date.value.split('.'))

            if not (1 <= month <= 12):
                raise ValueError("Miesiąc musi być między 01 a 12")

            if not (1 <= day <= 31):
                raise ValueError("Dzień musi być między 01 a 31")

            if month in [4, 6, 9, 11] and day > 30:
                raise ValueError(f"{month} miesiąc ma tylko 30 dni!")

            if month == 2 and day > 28:
                raise ValueError("Luty ma maksymalnie 28 dni!")

            year = today.year
            if month < today.month or (month == today.month and day < today.day):
                year += 1

            start_date = f"{year}-{month:02d}-{day:02d}"
            datetime.datetime.strptime(start_date, "%Y-%m-%d")  # Rzuca ValueError jeśli data nie istnieje

            cog.absences['absences'].append({
                'user_id': str(interaction.user.id),
                'type': 'daily',
                'start_date': start_date,
                'end_date': start_date
            })

            channel = interaction.client.get_channel(ABSENCE_CHANNEL_ID)
            await cog.update_absence_embed(channel)
            cog.save_data()

            formatted_date = cog.format_date_with_weekday(start_date)
            await interaction.response.send_message(
                f"-# ✅ Zgłoszono nieobecność na dzień {formatted_date}!",
                ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Błąd: {str(e)}\nPoprawny format: DD.MM (np. 15.06)",
                ephemeral=True
            )
        except Exception as e:
            print(f"Nieoczekiwany błąd w DailyAbsenceModal: {e}")
            await interaction.response.send_message(
                "❌ Wystąpił nieoczekiwany błąd! Proszę powiadomić administratora.",
                ephemeral=True
            )


class PeriodAbsenceModal(ui.Modal, title="Zgłoś dłuższą nieobecność"):
    start_date = ui.TextInput(
        label="Data początkowa (DD.MM)",
        placeholder="np. 15.06",
        required=True,
        max_length=5,
        min_length=4
    )

    end_date = ui.TextInput(
        label="Data końcowa (DD.MM)",
        placeholder="np. 20.06",
        required=True,
        max_length=5,
        min_length=4
    )

    async def parse_and_validate_date(self, date_str: str) -> str:
        """Parsuje i waliduje datę w formacie DD.MM, zwraca YYYY-MM-DD"""
        if '.' not in date_str or len(date_str.split('.')) != 2:
            raise ValueError("Użyj formatu DD.MM")

        day, month = map(int, date_str.split('.'))

        if not (1 <= month <= 12):
            raise ValueError("Miesiąc musi być między 01 a 12")

        if not (1 <= day <= 31):
            raise ValueError("Dzień musi być między 01 a 31")

        if month in [4, 6, 9, 11] and day > 30:
            raise ValueError(f"{month} miesiąc ma tylko 30 dni!")

        if month == 2 and day > 28:
            raise ValueError("Luty ma maksymalnie 28 dni!")

        today = datetime.date.today()
        year = today.year
        if month < today.month or (month == today.month and day < today.day):
            year += 1

        return f"{year}-{month:02d}-{day:02d}"

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("NieobecnosciSystem")

        try:
            start_date = await self.parse_and_validate_date(self.start_date.value)
            end_date = await self.parse_and_validate_date(self.end_date.value)

            start_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

            if end_obj < start_obj:
                raise ValueError("Data końcowa nie może być wcześniejsza niż początkowa!")

            cog.absences['absences'].append({
                'user_id': str(interaction.user.id),
                'type': 'period',
                'start_date': start_date,
                'end_date': end_date
            })

            channel = interaction.client.get_channel(ABSENCE_CHANNEL_ID)
            await cog.update_absence_embed(channel)
            cog.save_data()

            formatted_start = cog.format_date_with_weekday(start_date)
            formatted_end = cog.format_date_with_weekday(end_date)
            await interaction.response.send_message(
                f"-# ✅ Zgłoszono nieobecność w okresie {formatted_start} do {formatted_end}!",
                ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Błąd: {str(e)}\nPoprawny format: DD.MM (np. 15.06)",
                ephemeral=True
            )
        except Exception as e:
            print(f"Nieoczekiwany błąd w PeriodAbsenceModal: {e}")
            await interaction.response.send_message(
                "❌ Wystąpił nieoczekiwany błąd! Proszę powiadomić administratora.",
                ephemeral=True
            )


class LateAbsenceModal(ui.Modal, title="Zgłoś spóźnienie"):
    date = ui.TextInput(
        label="Data (DD.MM)",
        placeholder="np. 15.06",
        required=True,
        max_length=5,
        min_length=4
    )

    async def on_submit(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog("NieobecnosciSystem")
        today = datetime.date.today()

        try:
            if '.' not in self.date.value or len(self.date.value.split('.')) != 2:
                raise ValueError("Użyj formatu DD.MM")

            day, month = map(int, self.date.value.split('.'))

            if not (1 <= month <= 12):
                raise ValueError("Miesiąc musi być między 01 a 12")

            if not (1 <= day <= 31):
                raise ValueError("Dzień musi być między 01 a 31")

            if month in [4, 6, 9, 11] and day > 30:
                raise ValueError(f"{month} miesiąc ma tylko 30 dni!")

            if month == 2 and day > 28:
                raise ValueError("Luty ma maksymalnie 28 dni!")

            year = today.year
            if month < today.month or (month == today.month and day < today.day):
                year += 1

            start_date = f"{year}-{month:02d}-{day:02d}"
            datetime.datetime.strptime(start_date, "%Y-%m-%d")

            cog.absences['absences'].append({
                'user_id': str(interaction.user.id),
                'type': 'late',
                'start_date': start_date,
                'end_date': start_date
            })

            channel = interaction.client.get_channel(ABSENCE_CHANNEL_ID)
            await cog.update_absence_embed(channel)
            cog.save_data()

            formatted_date = cog.format_date_with_weekday(start_date)
            await interaction.response.send_message(
                f"-# ✅ Zgłoszono spóźnienie na dzień {formatted_date}!",
                ephemeral=True
            )

        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Błąd: {str(e)}\nPoprawny format: DD.MM (np. 15.06)",
                ephemeral=True
            )
        except Exception as e:
            print(f"Nieoczekiwany błąd w LateAbsenceModal: {e}")
            await interaction.response.send_message(
                "❌ Wystąpił nieoczekiwany błąd! Proszę powiadomić administratora.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(NieobecnosciSystem(bot))