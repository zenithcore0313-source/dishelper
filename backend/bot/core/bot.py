import discord
from discord.ext import commands
import logging
from config import GUILD_ID
from bot.cogs.onboarding import VerifyButtonView, GameRoleSelectView
from bot.cogs.party_lfg import PartyHubView
from bot.cogs.moderation import TicketLaunchView, TicketCloseView

logger = logging.getLogger("DiscordBot")
logging.basicConfig(level=logging.INFO)

class GamingCommunityBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.voice_states = True
        intents.presences = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # 1. 재부팅되어도 버튼이 계속 작동하도록 Persistent View 등록
        self.add_view(VerifyButtonView())
        self.add_view(GameRoleSelectView())
        self.add_view(PartyHubView())
        self.add_view(TicketLaunchView())
        self.add_view(TicketCloseView())

        # 2. Cogs 로드
        cogs = [
            "bot.cogs.onboarding",
            "bot.cogs.party_lfg",
            "bot.cogs.voice_master",
            "bot.cogs.moderation",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension: {cog}")
            except Exception as e:
                logger.error(f"Failed to load extension {cog}: {e}")

        # 3. 슬래시 명령어 동기화
        if GUILD_ID:
            guild_obj = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
            logger.info(f"Synced slash commands to target guild: {GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("Synced global slash commands")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="성인 종합 게임 커뮤니티 케어 중"
            ),
            status=discord.Status.online
        )

bot_instance = GamingCommunityBot()
