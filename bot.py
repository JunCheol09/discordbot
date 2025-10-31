# bot.py
import os
import random
import logging
import traceback
import discord
from discord.ext import commands
from discord import app_commands

# ----------------- 설정 -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Render 환경변수 이름과 통일
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.members = True           # on_member_join에 필요
intents.message_content = True   # 텍스트 읽기(명령형 메시지 등), 선택
# intents.presences = True       # 필요하면 켜세요(Portal에서도 ON)

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------- 뷰/컴포넌트 -----------------
class EchoView(discord.ui.View):
    def __init__(self, text: str):
        super().__init__(timeout=60)
        self.text = text

    @discord.ui.button(label="다시 말해줘", style=discord.ButtonStyle.primary)
    async def echo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(self.text, ephemeral=True)

# ----------------- Cog(슬래시 명령어) -----------------
class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="핑 확인")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong! 🏓")

    @app_commands.command(name="echo", description="입력한 문장을 따라함")
    @app_commands.describe(text="봇이 따라할 내용")
    async def echo(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(f"말씀하신 내용: {text}", view=EchoView(text))

    @app_commands.command(name="roll", description="주사위를 굴립니다 (기본 6면)")
    async def roll(self, interaction: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6):
        await interaction.response.send_message(
            f"🎲 {sides}면 주사위 결과: **{random.randint(1, sides)}**"
        )

    @app_commands.command(name="userinfo", description="사용자 정보")
    async def userinfo(self, interaction: discord.Interaction, user: discord.User | None = None):
        user = user or interaction.user
        embed = discord.Embed(title="사용자 정보", color=discord.Color.blurple())
        embed.add_field(name="이름", value=str(user), inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

# ----------------- 이벤트 -----------------
@bot.event
async def on_ready():
    try:
        if not bot.get_cog("Basic"):
            await bot.add_cog(Basic(bot))
        # 글로벌 동기화 (최초엔 1~2분 지연될 수 있음)
        synced = await bot.tree.sync()
        logger.info(f"[READY] Synced {len(synced)} slash commands.")
    except Exception:
        logger.exception("[ERROR] Slash sync failed")
    logger.info(f"[READY] Logged in as {bot.user} (ID: {bot.user.id})")

@bot.event
async def on_member_join(member: discord.Member):
    # 1) 채널로 환영 메시지
    try:
        msg = f"{member.mention} 님 환영합니다! 🎉"
        channel = None
        if WELCOME_CHANNEL_ID:
            channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            channel = member.guild.system_channel or next(
                (c for c in member.guild.text_channels if c.permissions_for(member.guild.me).send_messages),
                None
            )
        if channel:
            await channel.send(msg)
    except Exception:
        logger.exception("[ERROR] on_member_join channel send failed")

    # 2) DM 환영 (실패해도 무시)
    try:
        await member.send(f"{member.display_name} 님 환영합니다! 서버 규칙을 꼭 확인해주세요 🙌")
    except discord.Forbidden:
        pass

@bot.event
async def on_error(event_method, *args, **kwargs):
    logger.error(f"[ERROR] {event_method}")
    traceback.print_exc()

# ----------------- 실행 -----------------
if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("환경변수 DISCORD_BOT_TOKEN 이 설정되지 않았습니다.")
    bot.run(TOKEN)
