import discord
from discord.ext import commands
import aiohttp
import io
import uuid
import datetime
import pytz
import json
import os

CONFIG_FILE = "info_channels.json"


async def fetch_image(url, session=None):
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
    except Exception as e:
        print(f"Failed to fetch image {url}: {e}")
    return None


class InfoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.info_api = "http://raw.thug4ff.com/info"
        self.profile_card_api = "http://profile.thug4ff.com/api/profile_card"
        self.outfit_api = "http://profile.thug4ff.com/api/profile"
        self.config_data = self.load_config()
        self.cooldowns = {}

    def load_config(self):
        default_config = {"servers": {}}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return default_config
        return default_config

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    async def is_channel_allowed(self, ctx):
        guild_id = str(ctx.guild.id)
        allowed_channels = self.config_data.get("servers", {}).get(guild_id, {}).get("info_channels", [])
        if not allowed_channels:
            return True
        return str(ctx.channel.id) in allowed_channels

    @commands.hybrid_command(name="setinfochannel", description="Set allowed channel for !info command")
    @commands.has_permissions(administrator=True)
    async def set_info_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        self.config_data.setdefault("servers", {}).setdefault(guild_id, {"info_channels": []})
        if str(channel.id) not in self.config_data["servers"][guild_id]["info_channels"]:
            self.config_data["servers"][guild_id]["info_channels"].append(str(channel.id))
            self.save_config()
            await ctx.send(f"✅ {channel.mention} is now allowed for `!info` commands")
        else:
            await ctx.send(f"ℹ️ {channel.mention} is already allowed")

    @commands.hybrid_command(name="removeinfochannel", description="Remove allowed channel for !info command")
    @commands.has_permissions(administrator=True)
    async def remove_info_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        if guild_id in self.config_data.get("servers", {}):
            if str(channel.id) in self.config_data["servers"][guild_id]["info_channels"]:
                self.config_data["servers"][guild_id]["info_channels"].remove(str(channel.id))
                self.save_config()
                await ctx.send(f"✅ {channel.mention} removed from allowed channels")
            else:
                await ctx.send(f"❌ {channel.mention} was not in allowed channels")
        else:
            await ctx.send("ℹ️ No configuration found for this server")

    @commands.hybrid_command(name="infochannels", description="List allowed channels for !info command")
    async def list_info_channels(self, ctx):
        guild_id = str(ctx.guild.id)
        allowed_channels = self.config_data.get("servers", {}).get(guild_id, {}).get("info_channels", [])
        if allowed_channels:
            channels = []
            for cid in allowed_channels:
                ch = ctx.guild.get_channel(int(cid))
                channels.append(f"• {ch.mention if ch else f'ID: {cid}'}")
            embed = discord.Embed(title="Allowed !info channels", description="\n".join(channels), color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Allowed !info channels", description="All channels allowed (no restriction)", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="info", description="Displays EM OFFICIAL player info")
    async def player_info(self, ctx: commands.Context, uid: str):
    
        if not await self.is_channel_allowed(ctx):
            return await ctx.send("❌ This command is not allowed in this channel.", ephemeral=True)

        # Cooldown: 10 sec per user
        now = datetime.datetime.now()
        last_used = self.cooldowns.get(ctx.author.id)
        if last_used and (now - last_used).seconds < 10:
            return await ctx.send(f"⏳ Please wait {10 - (now - last_used).seconds}s before using this command again", ephemeral=True)
        self.cooldowns[ctx.author.id] = now

        async with ctx.typing():
            try:
                async with self.session.get(f"{self.info_api}?uid={uid}") as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Could not fetch player info.")
                    data = await resp.json()

                b = data.get("basicInfo", {})
                c = data.get("clanBasicInfo", {})
                l = data.get("captainBasicInfo", {})
                s = data.get("socialInfo", {})
                prof = data.get("profileInfo", {})
                p = data.get("petInfo", {})
                credit = data.get("creditScoreInfo", {})
                d = data.get("diamondCostRes", {})

                np_time = datetime.datetime.now(pytz.timezone("Asia/Kathmandu")).strftime("%I:%M %p")

                def get(val): return val if val is not None else "Not found"
                def format_ts(ts):
                    try: return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
                    except: return "Not found"

                # Profile card
                profile_card_url = f"{self.profile_card_api}?uid={uid}"
                profile_img_bytes = await fetch_image(profile_card_url, session=self.session)
                file_profile_card = discord.File(io.BytesIO(profile_img_bytes), filename="profile_card.png") if profile_img_bytes else None

                # Outfit
                outfit_url = f"{self.outfit_api}?uid={uid}"
                outfit_bytes = await fetch_image(outfit_url, session=self.session)

                # Embed
                description = (
    f"**┌ PLAYER INFO**\n"
    f"**├─ Name**: {get(b.get('nickname'))}\n"
    f"**├─ UID**: `{get(b.get('accountId'))}`\n"
    f"**├─ Account Type**: {get(b.get('accountType'))}\n"
    f"**├─ Level**: {get(b.get('level'))} (Exp: {get(b.get('exp'))})\n"
    f"**├─ Region**: {get(b.get('region'))}\n"
    f"**├─ Likes**: {get(b.get('liked'))}\n"
    f"**├─ Honor Score**: {get(credit.get('creditScore'))}\n"
    f"**├─ Max BR Rank**: {get(b.get('maxRank'))}\n"
    f"**├─ Max CS Rank**: {get(b.get('csMaxRank'))}\n"
    f"**└─ Signature**: {get(s.get('signature'))}\n\n"

    f"**┌ ACCOUNT ACTIVITY**\n"
    f"**├─ Most Recent OB**: {get(b.get('releaseVersion'))}\n"
    f"**├─ BP Badges**: {get(b.get('badgeCnt'))}\n"
    f"**├─ Badge ID**: {get(b.get('badgeId'))}\n"
    f"**├─ Season ID**: {get(b.get('seasonId'))}\n"
    f"**├─ BR Rank Points**: {get(b.get('rankingPoints'))}\n"
    f"**├─ CS Rank Points**: {get(b.get('csRank'))}\n"
    f"**├─ Created At**: {format_ts(b.get('createAt'))}\n"
    f"**└─ Last Login**: {format_ts(b.get('lastLoginAt'))}\n\n"

    f"**┌ ACCOUNT OVERVIEW**\n"
    f"**├─ Avatar ID**: {get(prof.get('avatarId'))}\n"
    f"**├─ Head Pic**: {get(b.get('headPic'))}\n"
    f"**├─ Banner ID**: {get(b.get('bannerId'))}\n"
    f"**├─ Pin ID**: {get(b.get('pinId'))}\n"
    f"**├─ Title**: {get(b.get('title'))}\n"
    f"**├─ Clothes IDs**: {get(prof.get('clothes'))}\n"
    f"**└─ Equipped Skills**: {get(prof.get('equipedSkills'))}\n\n"

    f"**┌ PET DETAILS**\n"
    f"**├─ Equipped?**: {'Yes' if p.get('isSelected') else 'No'}\n"
    f"**├─ Pet ID**: {get(p.get('id'))}\n"
    f"**├─ Pet Name**: {get(p.get('name'))}\n"
    f"**├─ Pet Level**: {get(p.get('level'))}\n"
    f"**├─ Pet Exp**: {get(p.get('exp'))}\n"
    f"**├─ Skin ID**: {get(p.get('skinId'))}\n"
    f"**└─ Skill ID**: {get(p.get('selectedSkillId'))}\n\n"

    f"**┌ GUILD INFO**\n"
    f"**├─ Guild Name**: {get(c.get('clanName'))}\n"
    f"**├─ Guild ID**: `{get(c.get('clanId'))}`\n"
    f"**├─ Guild Level**: {get(c.get('clanLevel'))}\n"
    f"**├─ Capacity**: {get(c.get('capacity'))}\n"
    f"**├─ Live Members**: {get(c.get('memberNum'))}/{get(c.get('capacity'))}\n"
    f"**└─ Leader Info**:\n"
    f"    **├─ Leader Name**: {get(l.get('nickname'))}\n"
    f"    **├─ Leader UID**: `{get(l.get('accountId'))}`\n"
    f"    **├─ Account Type**: {get(l.get('accountType'))}\n"
    f"    **├─ Leader Level**: {get(l.get('level'))} (Exp: {get(l.get('exp'))})\n"
    f"    **├─ Region**: {get(l.get('region'))}\n"
    f"    **├─ Likes**: {get(l.get('liked'))}\n"
    f"    **├─ Head Pic**: {get(l.get('headPic'))}\n"
    f"    **├─ Banner ID**: {get(l.get('bannerId'))}\n"
    f"    **├─ Badge ID**: {get(l.get('badgeId'))}\n"
    f"    **├─ Season ID**: {get(l.get('seasonId'))}\n"
    f"    **├─ BR Rank Points**: {get(l.get('rankingPoints'))}\n"
    f"    **├─ CS Rank Points**: {get(l.get('csRank'))}\n"
    f"    **├─ Max BR Rank**: {get(l.get('maxRank'))}\n"
    f"    **├─ Max CS Rank**: {get(l.get('csMaxRank'))}\n"
    f"    **├─ Created At**: {format_ts(l.get('createAt'))}\n"
    f"    **└─ Last Login**: {format_ts(l.get('lastLoginAt'))}\n\n"

    f"**┌ SOCIAL INFO**\n"
    f"**├─ Language**: {get(s.get('language'))}\n"
    f"**├─ Battle Tags**: {get(s.get('battleTag'))}\n"
    f"**├─ Battle Tag Count**: {get(s.get('battleTagCount'))}\n"
    f"**└─ Rank Show**: {get(s.get('rankShow'))}\n\n"

    f"**┌ DIAMOND INFO**\n"
    f"**└─ Diamonds Spent**: {get(d.get('diamondCost'))}\n"
                )
                embed = discord.Embed(title="**EM OFFICIAL TEAM PLAYER INFO**", description=description, color=discord.Color.blue())
                if file_profile_card:
                    embed.set_image(url="attachment://profile_card.png")
                embed.set_footer(text=f"DEVELOPED BY EM OFFICIAL TEAM | TODAY AT {np_time}")
                embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

                await ctx.send(embed=embed, file=file_profile_card if file_profile_card else None)
                if outfit_bytes:
                    file_outfit = discord.File(io.BytesIO(outfit_bytes), filename="outfit.png")
                    await ctx.send(file=file_outfit)
                else:
                    await ctx.send("❌ Could not fetch Outfit image.")

            except Exception as e:
                await ctx.send(f"❌ Unexpected error: `{e}`")

    async def cog_unload(self):
        await self.session.close()


# Cog setup
async def setup(bot):
    await bot.add_cog(InfoCommands(bot))
    print("✅ InfoCommands cog loaded successfully!")
