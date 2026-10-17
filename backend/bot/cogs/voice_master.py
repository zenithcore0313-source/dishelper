import discord
from discord.ext import commands
from discord import app_commands
from database import record_temp_voice, remove_temp_voice, get_temp_voice, set_temp_voice_lock

TRIGGER_CHANNEL_NAME = "방 만들기"

class RenameVoiceModal(discord.ui.Modal, title="음성방 이름 변경"):
    new_name = discord.ui.TextInput(
        label="새 방 이름",
        placeholder="예: 듀오 랭크, 집중 플레이 등",
        required=True,
        max_length=30
    )

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.channel.edit(name=f"[음성] {self.new_name.value.strip()}")
            await interaction.response.send_message(f"방 이름이 `[음성] {self.new_name.value.strip()}`(으)로 변경되었습니다.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"[오류] 이름 변경 실패: {e}", ephemeral=True)


class LimitVoiceModal(discord.ui.Modal, title="인원수 제한 설정"):
    limit = discord.ui.TextInput(
        label="최대 접속 인원 (0 = 무제한)",
        placeholder="예: 2, 4, 5, 0",
        required=True,
        max_length=2
    )

    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.limit.value.strip())
            if 0 <= val <= 99:
                await self.channel.edit(user_limit=val)
                limit_text = f"{val}명" if val > 0 else "무제한"
                await interaction.response.send_message(f"최대 접속 인원이 `{limit_text}`(으)로 변경되었습니다.", ephemeral=True)
            else:
                await interaction.response.send_message("[입력 오류] 0부터 99 사이의 숫자를 입력해주세요.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("[입력 오류] 숫자만 입력 가능합니다.", ephemeral=True)


class VoiceControllerView(discord.ui.View):
    def __init__(self, channel_id: int, owner_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.owner_id = owner_id

    async def _check_owner(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("[권한 오류] 방장 또는 관리자만 방 설정을 변경할 수 있습니다.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="방 잠금 / 해제", style=discord.ButtonStyle.secondary)
    async def toggle_lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return

        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            return

        info = await get_temp_voice(self.channel_id)
        is_locked = bool(info.get("is_locked", 0)) if info else False
        new_locked = not is_locked

        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.connect = False if new_locked else None
        await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await set_temp_voice_lock(self.channel_id, new_locked)

        status_text = "잠김 (새 유저 입장 불가)" if new_locked else "잠금 해제 (자유 입장 가능)"
        await interaction.response.send_message(f"방 상태가 `{status_text}`(으)로 변경되었습니다.", ephemeral=True)

    @discord.ui.button(label="인원 제한", style=discord.ButtonStyle.secondary)
    async def set_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await interaction.response.send_modal(LimitVoiceModal(channel))

    @discord.ui.button(label="방 이름 변경", style=discord.ButtonStyle.secondary)
    async def rename_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_owner(interaction):
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await interaction.response.send_modal(RenameVoiceModal(channel))


class VoiceMasterCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.channel and after.channel.name == TRIGGER_CHANNEL_NAME:
            guild = member.guild
            category = after.channel.category

            channel_name = f"[음성] {member.display_name}"
            temp_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                user_limit=5
            )

            await member.move_to(temp_channel)
            await record_temp_voice(temp_channel.id, guild.id, member.id)

            embed = discord.Embed(
                title=f"{member.display_name}의 음성방",
                description=(
                    "임시 음성 채널이 생성되었습니다.\n"
                    "아래 버튼으로 인원 제한 및 방 설정을 조정할 수 있습니다.\n"
                    "*모든 인원이 퇴장하면 채널이 자동으로 삭제됩니다.*"
                ),
                color=discord.Color.from_rgb(71, 85, 105)
            )
            embed.add_field(name="방장", value=member.mention, inline=True)
            embed.add_field(name="기본 정원", value="5명", inline=True)
            embed.set_footer(text="ServerOS Voice Controller")

            view = VoiceControllerView(temp_channel.id, member.id)
            await temp_channel.send(embed=embed, view=view)

        if before.channel:
            temp_info = await get_temp_voice(before.channel.id)
            if temp_info and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="임시 음성방 전원 퇴장으로 정리")
                    await remove_temp_voice(before.channel.id)
                except Exception:
                    pass

    @app_commands.command(name="setup_voice_master", description="임시 음성방 자동 생성 시스템을 설정합니다")
    @app_commands.default_permissions(administrator=True)
    async def setup_voice_master(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = await guild.create_category("음성 채널")
        await guild.create_voice_channel(TRIGGER_CHANNEL_NAME, category=category)

        await interaction.response.send_message(
            f"[설치 완료] `음성 채널` 카테고리와 `{TRIGGER_CHANNEL_NAME}` 채널이 생성되었습니다.",
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceMasterCog(bot))
