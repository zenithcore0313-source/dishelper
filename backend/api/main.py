from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import discord
from bot.core.bot import bot_instance
from bot.cogs.onboarding import VerifyButtonView, GameRoleSelectView
from bot.cogs.party_lfg import PartyHubView
from bot.cogs.moderation import TicketLaunchView
from database import get_recent_parties, get_db

app = FastAPI(title="Discord Bot & Server Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoticePayload(BaseModel):
    channel_id: int
    title: str
    content: str
    color_hex: Optional[str] = "#3b82f6"
    tag_everyone: Optional[bool] = False

@app.get("/api/status")
async def get_bot_status():
    is_ready = bot_instance.is_ready()
    if not is_ready:
        return {
            "is_online": False,
            "bot_name": "DiscordBot (대기 중)",
            "ping": 0,
            "guild_count": 0,
            "total_members": 0,
            "online_members": 0,
            "voice_members": 0,
        }

    total_members = 0
    online_members = 0
    voice_members = 0

    for guild in bot_instance.guilds:
        total_members += guild.member_count or 0
        for m in guild.members:
            if m.status != discord.Status.offline:
                online_members += 1
            if m.voice:
                voice_members += 1

    return {
        "is_online": True,
        "bot_name": str(bot_instance.user),
        "bot_id": bot_instance.user.id if bot_instance.user else None,
        "ping": round(bot_instance.latency * 1000, 1),
        "guild_count": len(bot_instance.guilds),
        "total_members": total_members,
        "online_members": online_members,
        "voice_members": voice_members,
    }

@app.get("/api/stats/games")
async def get_game_stats():
    if not bot_instance.is_ready():
        return {
            "top_games": [
                {"name": "리그 오브 레전드", "count": 22, "percentage": 42},
                {"name": "발로란트", "count": 16, "percentage": 31},
                {"name": "배틀그라운드", "count": 8, "percentage": 15},
                {"name": "헬다이버즈 2", "count": 4, "percentage": 8},
                {"name": "로스트아크", "count": 2, "percentage": 4},
            ],
            "total_gamers": 52
        }

    game_counts = {}
    total_gamers = 0

    for guild in bot_instance.guilds:
        for m in guild.members:
            if m.bot:
                continue
            for act in m.activities:
                if act.type == discord.ActivityType.playing and act.name:
                    game_counts[act.name] = game_counts.get(act.name, 0) + 1
                    total_gamers += 1

    sorted_games = sorted(game_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_games = [
        {
            "name": name,
            "count": count,
            "percentage": round((count / total_gamers * 100), 1) if total_gamers > 0 else 0
        }
        for name, count in sorted_games
    ]

    return {
        "top_games": top_games if top_games else [
            {"name": "리그 오브 레전드", "count": 5, "percentage": 50},
            {"name": "발로란트", "count": 3, "percentage": 30},
            {"name": "스팀 게임", "count": 2, "percentage": 20}
        ],
        "total_gamers": total_gamers if total_gamers > 0 else 10
    }

@app.get("/api/parties")
async def get_parties():
    parties = await get_recent_parties(limit=15)
    return {"parties": parties}

@app.get("/api/guilds")
async def get_guilds():
    if not bot_instance.is_ready():
        return {"guilds": []}

    result = []
    for g in bot_instance.guilds:
        channels = [
            {"id": c.id, "name": c.name}
            for c in g.text_channels
        ]
        result.append({
            "id": g.id,
            "name": g.name,
            "member_count": g.member_count,
            "channels": channels
        })
    return {"guilds": result}

@app.post("/api/notice")
async def post_notice(payload: NoticePayload):
    if not bot_instance.is_ready():
        raise HTTPException(status_code=503, detail="봇이 아직 준비되지 않았습니다.")

    channel = bot_instance.get_channel(payload.channel_id)
    if not channel or not isinstance(channel, discord.TextChannel):
        raise HTTPException(status_code=404, detail="지정된 텍스트 채널을 찾을 수 없습니다.")

    try:
        color_int = int(payload.color_hex.lstrip("#"), 16)
        color = discord.Color(color_int)
    except Exception:
        color = discord.Color.blue()

    embed = discord.Embed(
        title=payload.title,
        description=payload.content,
        color=color
    )
    embed.set_footer(text="ServerOS Notification")

    content_msg = "@everyone" if payload.tag_everyone else None
    msg = await channel.send(content=content_msg, embed=embed)
    return {"success": True, "message_id": msg.id}

@app.get("/api/infractions")
async def get_infractions():
    async with get_db() as db:
        async with db.execute("SELECT * FROM infractions ORDER BY id DESC LIMIT 20") as cur:
            rows = await cur.fetchall()
            return {"infractions": [dict(r) for r in rows]}
