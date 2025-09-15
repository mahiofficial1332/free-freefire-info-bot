import discord
from discord.ext import commands
import aiohttp
import io
import uuid
import datetime
import pytz

OWNER_IDS = [1380183114109947924]  # Add more owner IDs if needed


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

    @commands.hybrid_command(name="info", description="Displays EM OFFICIAL player info")
    async def player_info(self, ctx: commands.Context, uid: str):
        if ctx.author.id not in OWNER_IDS:
            return await ctx.send("❌ You are not allowed to use this command.", ephemeral=True)

        async with ctx.typing():
            try:
                # Fetch player info
                async with self.session.get(f"{self.info_api}?uid={uid}") as resp:
                    if resp.status != 200:
                        return await ctx.send("❌ Could not fetch player info.")
                    data = await resp.json()

                # Extract data
                b = data.get("basicInfo", {})
                c = data.get("clanBasicInfo", {})
                l = data.get("captainBasicInfo", {})
                s = data.get("socialInfo", {})
                prof = data.get("profileInfo", {})
                p = data.get("petInfo", {})
                credit = data.get("creditScoreInfo", {})
                d = data.get("diamondCostRes", {})

                np_time = datetime.datetime.now(pytz.timezone("Asia/Kathmandu")).strftime("%I:%M %p")

                # Helper
                def get(val):
                    return val if val is not None else "Not found"

                def format_ts(ts):
                    try:
                        return datetime.datetime.utcfromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        return "Not found"

                # Fetch profile card image
                profile_card_url = f"{self.profile_card_api}?uid={uid}"
                profile_img_bytes = await fetch_image(profile_card_url, session=self.session)
                file_profile_card = None
                if profile_img_bytes:
                    file_profile_card = discord.File(io.BytesIO(profile_img_bytes), filename="profile_card.png")

                # Outfit URL
                outfit_url = f"{self.outfit_api}?uid={uid}"

                # Description
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
                    f"**└─ Diamonds Spent**: {get(d.get('diamondCost'))}\n\n"
                )

                embed = discord.Embed(
                    title="**EM OFFICIAL TEAM PLAYER INFO**",
                    description=description,
                    color=discord.Color.blue()
                )
                if file_profile_card:
                    embed.set_image(url="attachment://profile_card.png")
                embed.set_footer(text=f"DEVELOPED BY EM OFFICIAL TEAM | TODAY AT {np_time}")
                embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

                await ctx.send(embed=embed, file=file_profile_card if file_profile_card else None)

                # Send outfit image separately
                outfit_bytes = await fetch_image(outfit_url, session=self.session)
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
    """
    Adds the InfoCommands cog to the bot.
    """
    await bot.add_cog(InfoCommands(bot))
    print("✅ InfoCommands cog loaded successfully!")
