import discord
import requests
import math
import random
from discord.ext import commands
from discord import app_commands, Embed
from datetime import datetime, timezone
from config import WCL_API_KEY

class WowCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="solemnity", description="Wyświetla informacje o gildii Solemnity.")
    @app_commands.describe(raid_index="Indeks raidu")
    async def solemnity(self, interaction: discord.Interaction, raid_index: int = 1):
        await interaction.response.defer()

        url_guild = "https://raider.io/api/v1/guilds/profile"
        params_guild = {
            "region": "eu",
            "realm": "burning-legion",
            "name": "Solemnity",
            "fields": "raid_progression,raid_rankings"
        }

        try:
            response_guild = requests.get(url_guild, params=params_guild)
            response_guild.raise_for_status()
            data_guild = response_guild.json()

            guild_name = data_guild.get("name", "Solemnity")
            raid_progression = data_guild.get("raid_progression", {})
            raid_rankings = data_guild.get("raid_rankings", {})

            raid_list = list(raid_progression.keys())
            if not raid_list:
                await interaction.followup.send("❌ Brak danych o raidach.")
                return

            if raid_index < 0 or raid_index >= len(raid_list):
                await interaction.followup.send(f"❌ Nieprawidłowy indeks raidu. Dostępne raidy: 0-{len(raid_list) - 1}.")
                return

            current_raid = raid_list[raid_index]
            current_raid_data = raid_progression.get(current_raid, {})
            raid_summary = current_raid_data.get("summary", "Brak danych")
            mythic_bosses = current_raid_data.get("mythic_bosses_killed", 0)

            if current_raid in raid_rankings:
                mythic_rankings = raid_rankings[current_raid].get("mythic", {})
                world_rank = mythic_rankings.get("world", "Brak danych")
                region_rank = mythic_rankings.get("region", "Brak danych")
                realm_rank = mythic_rankings.get("realm", "Brak danych")
            else:
                world_rank = region_rank = realm_rank = "Brak danych"

            url_pulls = "https://raider.io/api/v1/raiding/raid-rankings"
            params_pulls = {
                "raid": current_raid,
                "difficulty": "mythic",
                "region": "eu",
                "realm": "burning-legion",
                "guilds": "2011892",
                "limit": 1,
                "page": 0
            }

            response_pulls = requests.get(url_pulls, params=params_pulls)
            response_pulls.raise_for_status()
            data_pulls = response_pulls.json()

            boss_list = []
            if "raidRankings" in data_pulls and data_pulls["raidRankings"]:
                ranking_data = data_pulls["raidRankings"][0]
                encounters_pulled = ranking_data.get("encountersPulled", [])
                for boss in encounters_pulled:
                    boss_name = boss.get("slug", "Unknown Boss").replace("-", " ").title()
                    num_pulls = boss.get("numPulls", "Brak danych")
                    is_defeated = boss.get("isDefeated", False)
                    best_percent = boss.get("bestPercent", 0)

                    if is_defeated:
                        boss_list.append(f"🔹 `{boss_name:<30}` {num_pulls} pulli")
                    else:
                        boss_list.append(f"❌ `{boss_name:<30}` {num_pulls} pulli (Najlepsza pullka: {best_percent}%)")

            if not boss_list:
                boss_list_message = "❌ Nie pulnięto żadnego bossa na Mythicu"
            else:
                boss_list_message = "\n".join(boss_list)

            embed = Embed(
                title=f"Informacje o {guild_name} 🔥",
                description=f"**Raid:** {current_raid}\n"
                            f"**Progress:** {raid_summary}\n\n"
                            f"**Rankingi:**\n"
                            f"🌍 Świat: {world_rank}\n"
                            f"🗺️ Region: {region_rank}\n"
                            f"🏞️ Realm: {realm_rank}\n\n"
                            f"**Pull count:**\n{boss_list_message}",
                color=discord.Color.gold()
            )

            file = discord.File("solemnity.png", filename="solemnity.png")
            embed.set_thumbnail(url="attachment://solemnity.png")
            embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")	
            await interaction.followup.send(embed=embed, file=file)

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(f"❌ Błąd podczas pobierania danych z Raider.io: {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił nieoczekiwany błąd: {e}")

    @app_commands.command(name="weekly", description="Pokazuje ile dungeonów Mythic+ postać zagrała w tym tygodniu.")
    @app_commands.describe(
        nick="Nazwy postaci (oddzielone spacjami)",
        realm="Serwer postaci (domyślnie burning-legion)"
    )
    async def weekly(self, interaction: discord.Interaction, nick: str, realm: str = "burning-legion"):
        await interaction.response.defer()
        characters = nick.split()
        
        if len(characters) == 1:
            await self.process_single_character(interaction, characters[0], realm)
            return

        try:
            results = []
            thumbnails = []
            
            for character in characters:
                url = "https://raider.io/api/v1/characters/profile"
                params = {
                    "region": "eu",
                    "realm": realm.lower(),
                    "name": character,
                    "fields": "mythic_plus_weekly_highest_level_runs,name,thumbnail_url"
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                character_name = data.get("name", character)
                weekly_runs = data.get("mythic_plus_weekly_highest_level_runs", [])
                num_runs = len(weekly_runs)
                thumbnail_url = data.get("thumbnail_url", "")
                
                if num_runs == 0:
                    results.append(f"💀 `{character_name:<10}` **0** dungów")
                elif num_runs == 1:
                    results.append(f"😂 `{character_name:<10}` **1** dung")
                elif 2 <= num_runs <= 4:
                    results.append(f"😐 `{character_name:<10}` **{num_runs}** dungi")
                elif 5 <= num_runs <= 7:
                    results.append(f"🤨 `{character_name:<10}` **{num_runs}** dungów")
                else:
                    results.append(f"😎 `{character_name:<10}` **{num_runs}** dungów")
               
                if thumbnail_url and not thumbnails:
                    thumbnails.append(thumbnail_url)
            
            embed = Embed(
                title=f"Weekly 🔻 Multisearch",
                description="\n".join(results),
                color=discord.Color.purple()
            )
            
            if thumbnails:
                embed.set_thumbnail(url=thumbnails[0])
                
            embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")
            await interaction.followup.send(embed=embed)

        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                await interaction.followup.send(f"❌ Nie znaleziono jednej z postaci na serwerze {realm}.")
            else:
                await interaction.followup.send(f"❌ Błąd podczas pobierania danych z Raider.io: {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił nieoczekiwany błąd: {e}")

    async def process_single_character(self, interaction: discord.Interaction, nick: str, realm: str):
        url = "https://raider.io/api/v1/characters/profile"
        params = {
            "region": "eu",
            "realm": realm.lower(),
            "name": nick,
            "fields": "mythic_plus_weekly_highest_level_runs"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            nick = data.get("name", nick)
            realm = data.get("realm", realm)
            weekly_runs = data.get("mythic_plus_weekly_highest_level_runs", [])
            num_runs = len(weekly_runs)
            thumbnail_url = data.get("thumbnail_url", "")
            
            if num_runs == 0:
                message = f"{nick} nie zagrał **żadnego** dunga w tym tygodniu 💀"
            elif num_runs == 1:
                message = f"{nick} zagrał **{num_runs}** dunga w tym tygodniu 😂"
            elif 2 <= num_runs <= 4:
                message = f"{nick} zagrał **{num_runs}** dungi w tym tygodniu 😐"
            elif 5 <= num_runs <= 7:
                message = f"{nick} zagrał **{num_runs}** dungów w tym tygodniu 🤨"
            else:
                message = f"{nick} zagrał **{num_runs}** dungów w tym tygodniu 😎👍"

            embed = Embed(
                title=f"Weekly 🔻 {nick} | {realm}",
                description=message,
                color=discord.Color.purple()
            )
            
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
                
            embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")
            await interaction.followup.send(embed=embed)

        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                await interaction.followup.send(f"❌ Nie znaleziono postaci {nick} na serwerze {realm}.")
            else:
                await interaction.followup.send(f"❌ Błąd podczas pobierania danych z Raider.io: {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił nieoczekiwany błąd: {e}")
            
    @app_commands.command(name="logs", description="Pokazuje statystyki postaci z Warcraft Logs")
    @app_commands.describe(
        nick="Nazwa postaci",
        serwer="Serwer postaci (domyślnie burning-legion)",
        tryb="Tryb raidu: M (Mythic) lub HC (Heroic) (domyślnie M)"
    )
    async def logs(self, interaction: discord.Interaction, nick: str, serwer: str = "burning-legion", tryb: str = "M"):
        await interaction.response.defer()
        
        WCL_BASE_URL = "https://www.warcraftlogs.com/v1/rankings/character"
        RIO_BASE_URL = "https://raider.io/api/v1/characters/profile"
        
        difficulty_map = {
            "M": 5,
            "HC": 4
        }
        
        tryb = tryb.upper()
        if tryb not in difficulty_map:
            await interaction.followup.send("❌ Nieprawidłowy tryb. Dostępne opcje: M (Mythic) lub HC (Heroic)")
            return
        
        target_difficulty = difficulty_map[tryb]

        try:
            rio_params = {
                "region": "eu",
                "realm": serwer.lower(),
                "name": nick,
                "fields": "thumbnail_url"
            }
            rio_response = requests.get(RIO_BASE_URL, params=rio_params)
            rio_response.raise_for_status()
            rio_data = rio_response.json()
            thumbnail_url = rio_data.get("thumbnail_url", "")
            
            wcl_url = f"{WCL_BASE_URL}/{nick}/{serwer}/EU?timeframe=historical&api_key={WCL_API_KEY}"
            wcl_response = requests.get(wcl_url)
            wcl_response.raise_for_status()
            logs_data = wcl_response.json()
            
            if not logs_data:
                await interaction.followup.send(f"❌ Brak danych logów dla postaci {nick} na serwerze {serwer}")
                return
            
            character_class = logs_data[0].get("class", "Nieznana klasa")
            character_spec = logs_data[0].get("spec", "")
            server_name = logs_data[0].get("server", serwer)
            formatted_nick = nick.capitalize()
            
            results = []
            for encounter in logs_data:
                if encounter.get("difficulty") != target_difficulty:
                    continue
                    
                boss_name = encounter.get("encounterName", "Nieznany boss")
                percentile = math.floor(encounter.get("percentile", 0))
                
                if percentile < 25:
                    results.append(f"🔸 `{boss_name:<30}` <:gagaga:1276850810587840512> **{percentile}**")
                elif 25 <= percentile < 50:
                    results.append(f"🔸 `{boss_name:<30}` 🟩 **{percentile}**")
                elif 50 <= percentile < 75:
                    results.append(f"🔸 `{boss_name:<30}` 🟦 **{percentile}**")
                elif 75 <= percentile < 95:
                    results.append(f"🔸 `{boss_name:<30}` 🟪 **{percentile}**")
                elif 95 <= percentile < 99:
                    results.append(f"🔸 `{boss_name:<30}` 🟧 **{percentile}**")
                elif 99 <= percentile < 100:
                    results.append(f"🔸 `{boss_name:<30}` 🩷 **{percentile}**")
                else:
                    results.append(f"🔸 `{boss_name:<30}` 💛 **{percentile}**")
            
            if not results:
                await interaction.followup.send(f"❌ Brak logów na difficulty {'Mythic' if tryb == 'M' else 'Heroic'} dla postaci {formatted_nick}")
                return
            
            embed = discord.Embed(
                title=f"Logi 🔻 {formatted_nick} | {server_name} | {'Mythic' if tryb == 'M' else 'Heroic'}",
                description=f"{character_class} | {character_spec}\n\n" + "\n".join(results[:15]),
                color=discord.Color.purple()
            )
            
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            
            embed.set_footer(text=f"{interaction.guild.name} • {self.bot.user.name}")
            await interaction.followup.send(embed=embed)
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                await interaction.followup.send(f"❌ Nie znaleziono postaci {formatted_nick} na serwerze {serwer}")
            else:
                await interaction.followup.send(f"❌ Błąd podczas pobierania danych: {e}")
        except Exception as e:
            await interaction.followup.send(f"❌ Wystąpił nieoczekiwany błąd: {e}")

async def setup(bot):
    await bot.add_cog(WowCommands(bot))