import discord
from discord.ext import commands
from discord import app_commands
import json
from database import create_party, get_party, update_party_members, close_party, update_party_message

class PartyActionView(discord.ui.View):
    def __init__(self, party_id: int):
        super().__init__(timeout=None)
        self.party_id = party_id

    @discord.ui.button(label="파티 참가", style=discord.ButtonStyle.primary, custom_id="btn_join_party")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        party = await get_party(self.party_id)
        if not party:
            await interaction.response.send_message("[오류] 파티 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        if party["status"] == "closed":
            await interaction.response.send_message("이미 마감된 파티입니다.", ephemeral=True)
            return

        members = json.loads(party["current_members"])
        user_ids = [m["id"] for m in members]

        if interaction.user.id in user_ids:
            await interaction.response.send_message("이미 참여 중인 파티입니다.", ephemeral=True)
            return

        if len(members) >= party["max_members"]:
            await interaction.response.send_message("파티 인원이 가득 찼습니다.", ephemeral=True)
            return

        members.append({"id": interaction.user.id, "name": interaction.user.display_name})
        new_status = "full" if len(members) >= party["max_members"] else "open"
        await update_party_members(self.party_id, members, new_status)

        embed = interaction.message.embeds[0]
        member_names = [f"• <@{m['id']}> ({m['name']})" for m in members]
        embed.set_field_at(
            1,
            name=f"현재 인원 ({len(members)}/{party['max_members']})",
            value="\n".join(member_names),
            inline=False
        )

        if new_status == "full":
            embed.color = discord.Color.from_rgb(100, 116, 139)
            embed.title = f"[모집 마감] {party['game_name']} - {party['title']}"
            await interaction.response.edit_message(embed=embed, view=self)
            mentions = " ".join([f"<@{m['id']}>" for m in members])
            await interaction.followup.send(f"[파티 모집 완료]\n{mentions}\n인원이 모두 충원되었습니다. 음성 채널로 이동해주세요.")
        else:
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.followup.send(f"**{interaction.user.display_name}**님이 파티에 참가했습니다.", ephemeral=True)

    @discord.ui.button(label="참가 취소", style=discord.ButtonStyle.secondary, custom_id="btn_leave_party")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        party = await get_party(self.party_id)
        if not party:
            await interaction.response.send_message("[오류] 파티 정보를 찾을 수 없습니다.", ephemeral=True)
            return

        members = json.loads(party["current_members"])
        user_ids = [m["id"] for m in members]

        if interaction.user.id not in user_ids:
            await interaction.response.send_message("참여 중인 파티가 아닙니다.", ephemeral=True)
            return

        if interaction.user.id == party["leader_id"]:
            await close_party(self.party_id)
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.dark_grey()
            embed.title = f"[취소됨] {party['game_name']} - {party['title']}"
            self.stop()
            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send("파티장이 참가를 취소하여 파티가 해산되었습니다.")
            return

        members = [m for m in members if m["id"] != interaction.user.id]
        await update_party_members(self.party_id, members, "open")

        embed = interaction.message.embeds[0]
        member_names = [f"• <@{m['id']}> ({m['name']})" for m in members]
        embed.color = discord.Color.from_rgb(51, 65, 85)
        embed.title = f"[모집 중] {party['game_name']} - {party['title']}"
        embed.set_field_at(
            1,
            name=f"현재 인원 ({len(members)}/{party['max_members']})",
            value="\n".join(member_names) if member_names else "없음",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send("파티 참가를 취소했습니다.", ephemeral=True)

    @discord.ui.button(label="모집 마감", style=discord.ButtonStyle.secondary, custom_id="btn_close_party")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        party = await get_party(self.party_id)
        if not party:
            return

        is_admin = interaction.user.guild_permissions.administrator
        if interaction.user.id != party["leader_id"] and not is_admin:
            await interaction.response.send_message("[권한 오류] 파티장 또는 관리자만 파티를 마감할 수 있습니다.", ephemeral=True)
            return

        await close_party(self.party_id)
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.dark_grey()
        embed.title = f"[모집 마감] {party['game_name']} - {party['title']}"
        self.stop()
        await interaction.response.edit_message(embed=embed, view=None)
        await interaction.followup.send("파티 모집이 마감되었습니다.")


class CreatePartyModal(discord.ui.Modal, title="새 파티 모집 생성"):
    game_name = discord.ui.TextInput(
        label="게임 종류",
        placeholder="예: 리그 오브 레전드, 발로란트, 배틀그라운드 등",
        required=True,
        max_length=30
    )
    title_input = discord.ui.TextInput(
        label="모집 제목",
        placeholder="예: 2판 가볍게 즐겜하실 분",
        required=True,
        max_length=50
    )
    max_count = discord.ui.TextInput(
        label="목표 총 인원수 (숫자만)",
        placeholder="예: 5",
        default="5",
        required=True,
        max_length=2
    )
    memo = discord.ui.TextInput(
        label="추가 안내 사항 (선택)",
        placeholder="예: 티어 무관, 마이크 권장",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            max_num = int(self.max_count.value.strip())
            if max_num < 2 or max_num > 30:
                await interaction.response.send_message("[입력 오류] 인원수는 2명 이상 30명 이하로 입력해주세요.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("[입력 오류] 인원수는 숫자만 입력해주세요.", ephemeral=True)
            return

        party_id = await create_party(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            leader_id=interaction.user.id,
            leader_name=interaction.user.display_name,
            game_name=self.game_name.value.strip(),
            title=self.title_input.value.strip(),
            max_members=max_num
        )

        embed = discord.Embed(
            title=f"[모집 중] {self.game_name.value.strip()} - {self.title_input.value.strip()}",
            description=f"**파티장**: {interaction.user.mention} ({interaction.user.display_name})\n"
                        f"**메모**: {self.memo.value.strip() if self.memo.value else '자유롭게 참가해주세요.'}",
            color=discord.Color.from_rgb(51, 65, 85)
        )
        embed.add_field(name="게임", value=self.game_name.value.strip(), inline=True)
        embed.add_field(
            name=f"현재 인원 (1/{max_num})",
            value=f"• {interaction.user.mention} (파티장)",
            inline=False
        )
        embed.set_footer(text=f"Party #{party_id} | 참가 버튼을 눌러 등록하세요")

        view = PartyActionView(party_id)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        await update_party_message(party_id, msg.id)


class PartyHubView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="파티 구인 등록",
        style=discord.ButtonStyle.primary,
        custom_id="btn_open_party_modal"
    )
    async def create_party_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CreatePartyModal())


class PartyLFGCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup_party_hub", description="파티 구인 원터치 패널을 설치합니다")
    @app_commands.default_permissions(administrator=True)
    async def setup_party_hub(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="파티 구인 센터 (LFG)",
            description=(
                "함께 게임할 멤버를 모집할 수 있는 패널입니다.\n"
                "아래 **[파티 구인 등록]** 버튼을 누르시면 모집 양식이 열립니다.\n\n"
                "**기능 안내**\n"
                "• 버튼 클릭으로 즉시 파티 참가 및 취소\n"
                "• 정원 충원 시 파티원 일괄 자동 호출\n"
                "• 파티장 전용 마감 및 취소 지원"
            ),
            color=discord.Color.from_rgb(71, 85, 105)
        )
        embed.set_footer(text="ServerOS LFG System")
        await interaction.channel.send(embed=embed, view=PartyHubView())
        await interaction.response.send_message("[설치 완료] 파티 구인 패널이 배치되었습니다.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PartyLFGCog(bot))
