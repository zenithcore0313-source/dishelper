import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from datetime import datetime
from database import get_db

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="티켓 상담 종료", style=discord.ButtonStyle.secondary, custom_id="btn_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("티켓을 종료합니다...")
        if isinstance(interaction.channel, discord.Thread):
            await interaction.channel.edit(archived=True, locked=True)
        else:
            try:
                await interaction.channel.delete(reason="관리자/신고자 티켓 종료")
            except Exception:
                pass


class TicketLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="1:1 문의 및 비밀 신고 접수",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_open_report_ticket"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        channel = interaction.channel
        thread_name = f"문의-{user.display_name[:10]}-{user.id % 1000}"

        try:
            thread = await channel.create_thread(
                name=thread_name,
                auto_archive_duration=1440,
                type=discord.ChannelType.private_thread
            )
            await thread.add_user(user)
        except Exception:
            thread = await channel.create_thread(
                name=thread_name,
                auto_archive_duration=1440
            )

        embed = discord.Embed(
            title="1:1 관리자 상담 및 신고 접수",
            description=(
                f"{user.mention}님, 문의 또는 신고 내용을 남겨주세요.\n\n"
                "• 비매너 유저 신고 시 대상 닉네임과 상황 정황(스크린샷 등)을 남겨주세요.\n"
                "• 관리자가 내용을 확인한 후 답변을 드립니다.\n"
                "• 상담이 완료되면 아래 [티켓 상담 종료] 버튼을 눌러주세요."
            ),
            color=discord.Color.from_rgb(71, 85, 105)
        )
        embed.set_footer(text="ServerOS Moderation Hotline")

        await thread.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"비공개 상담 티켓이 생성되었습니다: {thread.mention}", ephemeral=True)


class ModerationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup_ticket_hub", description="1:1 문의 및 비밀 신고 패널을 설치합니다")
    @app_commands.default_permissions(administrator=True)
    async def setup_ticket_hub(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="관리자 1:1 상담 및 신고 창구",
            description=(
                "서버 내 매너 위반 행위 및 문의 사항을 접수합니다.\n\n"
                "• 비매너 언행 및 규정 위반 신고\n"
                "• 고의적인 게임 파토 및 분쟁 중재\n"
                "• 기타 서버 건의 및 질문\n\n"
                "아래 버튼을 누르면 관리자와의 비공개 1:1 창구가 생성됩니다."
            ),
            color=discord.Color.from_rgb(51, 65, 85)
        )
        await interaction.channel.send(embed=embed, view=TicketLaunchView())
        await interaction.response.send_message("[설치 완료] 신고/문의 패널이 배치되었습니다.", ephemeral=True)

    @app_commands.command(name="warn", description="유저에게 이용 수칙 위반 경고를 부여합니다")
    @app_commands.default_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, target: discord.Member, reason: str):
        async with await get_db() as db:
            await db.execute("""
                INSERT INTO infractions (guild_id, user_id, moderator_id, reason, action_type, created_at)
                VALUES (?, ?, ?, ?, 'warn', ?)
            """, (interaction.guild_id, target.id, interaction.user.id, reason, datetime.now().isoformat()))
            await db.commit()

            async with db.execute("SELECT COUNT(*) FROM infractions WHERE user_id = ? AND guild_id = ?", (target.id, interaction.guild_id)) as cur:
                count = (await cur.fetchone())[0]

        embed = discord.Embed(
            title="[경고 조치 알림]",
            description=f"{target.mention}님에게 이용 규정 위반 경고가 부여되었습니다. (누적 {count}회)\n**사유**: {reason}",
            color=discord.Color.from_rgb(180, 83, 9)
        )
        await interaction.response.send_message(embed=embed)

        try:
            dm_embed = discord.Embed(
                title=f"[{interaction.guild.name}] 규정 위반 경고 안내",
                description=f"관리자로부터 경고 조치를 받으셨습니다.\n**사유**: {reason}\n**누적 횟수**: {count}회\n(3회 이상 누적 시 제재 조치될 수 있습니다.)",
                color=discord.Color.from_rgb(180, 83, 9)
            )
            await target.send(embed=dm_embed)
        except Exception:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
