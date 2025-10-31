# bot.py
import os, asyncio, random, logging, traceback
import discord
from discord.ext import commands
from discord import app_commands
from aiohttp import web  # ✅ 작은 웹서버

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("discord-bot")

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))

# ----- Discord Intents (포털에서 켠 것과 동일하게) -----
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# intents.presences = True  # 필요 시 포털에서도 ON

bot = commands.Bot(command_prefix="!", intents=intents)

# ----- 슬래시 커맨드 -----
class Basic(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @app_commands.command(name="ping", description="핑 확인")
    async def ping(self, itx: discord.Interaction):
        await itx.response.send_message("Pong! 🏓")

    @app_commands.command(name="roll", description="주사위를 굴립니다")
    async def roll(self, itx: discord.Interaction, sides: app_commands.Range[int, 2, 1000] = 6):
        await itx.response.send_message(f"🎲 {sides}면: **{random.randint(1, sides)}**")

@bot.event
async def on_ready():
    try:
        if not bot.get_cog("Basic"):
            await bot.add_cog(Basic(bot))
        synced = await bot.tree.sync()   # 글로벌 동기화
        log.info(f"[READY] Synced {len(synced)} commands")
    except Exception:
        log.exception("Slash sync failed")
    log.info(f"[READY] Logged in as {bot.user} ({bot.user.id})")

@bot.event
async def on_member_join(member: discord.Member):
    try:
        msg = f"{member.mention} 님 환영합니다! 🎉"
        ch = None
        if WELCOME_CHANNEL_ID:
            ch = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not ch:
            ch = member.guild.system_channel or next(
                (c for c in member.guild.text_channels if c.permissions_for(member.guild.me).send_messages), None
            )
        if ch:
            await ch.send(msg)
        try:
            await member.send(f"{member.display_name} 님 환영합니다! 규칙을 확인해주세요 🙌")
        except discord.Forbidden:
            pass
    except Exception:
        log.exception("on_member_join failed")

# ----- 아주 작은 웹서버: Render 포트 바인딩 -----
async def health(request): return web.Response(text="ok")
async def run_web():
    app = web.Application()
    app.add_routes([web.get("/", health), web.get("/healthz", health)])
    port = int(os.environ.get("PORT", "10000"))  # Render가 PORT 제공
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"Web server listening on :{port}")
    while True:
        await asyncio.sleep(3600)

async def main():
    if not TOKEN:
        raise RuntimeError("환경변수 DISCORD_BOT_TOKEN 이 없습니다.")
    # 웹서버와 봇을 동시에 실행
    asyncio.create_task(run_web())
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
