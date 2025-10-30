import os, random, logging, discord
from discord.ext import commands
from discord import app_commands, Interaction

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-bot")

# 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---- 버튼 예시 ----
class EchoView(discord.ui.View):
    def __init__(self, text):
        super().__init__(timeout=60)
        self.text = text

    @discord.ui.button(label="다시 말해줘", style=discord.ButtonStyle.primary)
    async def echo_button(self, interaction, button):
        await interaction.response.send_message(self.text, ephemeral=True)

# ---- 기본 기능 ----
class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="핑 확인")
    async def ping(self, interaction):
        await interaction.response.send_message("Pong! 🏓")

    @app_commands.command(name="echo", description="입력한 문장을 따라함")
    @app_commands.describe(text="봇이 따라할 내용")
    async def echo(self, interaction, text: str):
        await interaction.response.send_message(f"말씀하신 내용: {text}", view=EchoView(text))

    @app_commands.command(name="roll", description="주사위를 굴립니다 (기본 6면)")
    async def roll(self, interaction, sides: app_commands.Range[int, 2, 1000] = 6):
        await interaction.response.send_message(
            f"🎲 {sides}면 주사위 결과: **{random.randint(1, sides)}**"
        )

    @app_commands.command(name="userinfo", description="사용자 정보")
    async def userinfo(self, interaction, user: discord.User = None):
        user = user or interaction.user
        embed = discord.Embed(title="사용자 정보", color=discord.Color.blurple())
        embed.add_field(name="이름", value=str(user), inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.set_thumbnail(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

@bot.event
async def on_ready():
    if not bot.get_cog("Basic"):
        await bot.add_cog(Basic(bot))
    await bot.tree.sync()
    logger.info(f"Logged in as {bot.user}")




if __name__ == "__main__":
    import os
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN 환경변수가 없습니다.")
    bot.run(token)