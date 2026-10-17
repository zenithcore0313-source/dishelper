import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from config import POPULAR_GAMES
from database import record_verification, is_user_verified

VERIFIED_ROLE_NAME = "인증 멤버"

class AdultVerifyModal(discord.ui.Modal, title="성인 인증 및 규칙 동의"):
    birth_year = discord.ui.TextInput(
        label="출생년도 (4자리 숫자)",
        placeholder="예: 1998",
        min_length=4,
        max_length=4,
        required=True
    )
    pledge = discord.ui.TextInput(
        label="매너 서약",
        placeholder="'매너를 준수하겠습니다'를 입력해주세요.",
        default="매너를 준수하겠습니다",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            year = int(self.birth_year.value.strip())
            current_year = datetime.now().year
            age = current_year - year + 1

            if age < 19 or year < 1920 or year > (current_year - 18):
                await interaction.response.send_message(
                    "[인증 실패] 만 19세 미만 미성년자는 본 서버를 이용하실 수 없습니다.",
                    ephemeral=True
                )
                return

            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("[오류] 서버 내부에서만 인증 가능합니다.", ephemeral=True)
                return

            role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
            if not role:
                try:
                    role = await guild.create_role(name=VERIFIED_ROLE_NAME, color=discord.Color.from_rgb(100, 116, 139), mentionable=True)
                except Exception:
                    pass

            if role:
                await interaction.user.add_roles(role)

            await record_verification(interaction.user.id, year)

            embed = discord.Embed(
                title="인증 완료",
                description=f"**{interaction.user.display_name}**님의 성인 인증이 완료되었습니다.\n`{VERIFIED_ROLE_NAME}` 역할이 지급되어 서버 내 모든 채널을 이용하실 수 있습니다.",
                color=discord.Color.from_rgb(71, 85, 105)
            )
            embed.set_footer(text="ServerOS Verification System")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            await interaction.response.send_message("[입력 오류] 출생년도는 숫자 4자리로 정확히 입력해주세요.", ephemeral=True)


class VerifyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="성인 인증 및 이용 규칙 동의",
        style=discord.ButtonStyle.primary,
        custom_id="btn_adult_verify"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await is_user_verified(interaction.user.id):
            await interaction.response.send_message("이미 인증이 완료된 계정입니다.", ephemeral=True)
            return
        await interaction.response.send_modal(AdultVerifyModal())


class GameRoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=g["label"],
                value=g["value"],
                description=g["description"]
            )
            for g in POPULAR_GAMES
        ]
        super().__init__(
            placeholder="플레이하는 게임을 선택하세요 (다중 선택 가능)",
            min_values=1,
            max_values=len(options),
            custom_id="select_game_roles",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # 3초 타임아웃 방지 (역할 생성 및 지급에 시간이 걸릴 수 있음)
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return

        selected_values = set(self.values)
        roles_to_add = []
        roles_to_remove = []
        added_labels = []
        removed_labels = []

        for g in POPULAR_GAMES:
            role_name = g["label"]
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                try:
                    role = await guild.create_role(name=role_name, mentionable=True)
                except Exception:
                    continue

            if g["value"] in selected_values:
                if role not in interaction.user.roles:
                    roles_to_add.append(role)
                    added_labels.append(g["label"])
            else:
                if role in interaction.user.roles:
                    roles_to_remove.append(role)
                    removed_labels.append(g["label"])

        try:
            if roles_to_add:
                await interaction.user.add_roles(*roles_to_add)
            if roles_to_remove:
                await interaction.user.remove_roles(*roles_to_remove)
        except discord.Forbidden:
            await interaction.followup.send("[권한 오류] 봇에게 '역할 관리' 권한이 없거나, 봇의 역할이 지급할 역할보다 위에 위치해야 합니다.", ephemeral=True)
            return

        msg_parts = []
        if added_labels:
            msg_parts.append(f"[추가] {', '.join(added_labels)}")
        if removed_labels:
            msg_parts.append(f"[제거] {', '.join(removed_labels)}")

        if not msg_parts:
            msg_parts.append("선택된 역할 변경사항이 없습니다.")

        await interaction.followup.send("\n".join(msg_parts), ephemeral=True)


class GameRoleSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GameRoleSelect())


class OnboardingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup_onboarding", description="채널에 성인 인증 및 게임 역할 선택 패널을 설치합니다")
    @app_commands.default_permissions(administrator=True)
    async def setup_onboarding(self, interaction: discord.Interaction):
        verify_embed = discord.Embed(
            title="성인 종합 게임 커뮤니티 — 본인 확인 및 이용 수칙",
            description=(
                "본 서버는 **만 19세 이상 성인**을 위한 게임 공간입니다.\n\n"
                "**기본 이용 수칙**\n"
                "• 만 19세 이상만 이용 가능 (미성년자 확인 시 제재)\n"
                "• 음주 후 과격한 언행, 욕설, 성희롱 엄금\n"
                "• 상호 존중 및 비매너 행위 지양\n"
                "• 분쟁 발생 시 1:1 신고 티켓 창구 이용\n\n"
                "아래 버튼을 눌러 출생년도를 입력하고 서약하시면 이용 권한이 부여됩니다."
            ),
            color=discord.Color.from_rgb(51, 65, 85)
        )
        verify_embed.set_footer(text="ServerOS Verification System")

        game_embed = discord.Embed(
            title="게임 역할 선택",
            description=(
                "플레이하시는 게임을 선택하시면 해당 게임의 모집 알림 멘션을 수신하실 수 있습니다.\n"
                "언제든지 다시 선택하여 변경할 수 있습니다."
            ),
            color=discord.Color.from_rgb(71, 85, 105)
        )

        await interaction.channel.send(embed=verify_embed, view=VerifyButtonView())
        await interaction.channel.send(embed=game_embed, view=GameRoleSelectView())
        await interaction.response.send_message("[설치 완료] 온보딩 패널 2종이 배치되었습니다.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(OnboardingCog(bot))
