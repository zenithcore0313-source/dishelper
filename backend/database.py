import aiosqlite
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager
from config import DATABASE_PATH

@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # 성인 인증 유저
        await db.execute("""
            CREATE TABLE IF NOT EXISTS verified_users (
                user_id INTEGER PRIMARY KEY,
                birth_year INTEGER,
                agreed_rules INTEGER DEFAULT 1,
                verified_at TEXT
            )
        """)
        # 유저 선호 게임 태그
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_games (
                user_id INTEGER,
                game_key TEXT,
                PRIMARY KEY (user_id, game_key)
            )
        """)
        # 파티 구인(LFG) 목록
        await db.execute("""
            CREATE TABLE IF NOT EXISTS parties (
                party_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER,
                message_id INTEGER,
                leader_id INTEGER,
                leader_name TEXT,
                game_name TEXT,
                title TEXT,
                max_members INTEGER,
                current_members TEXT, -- JSON array of user_ids and names
                voice_channel_id INTEGER,
                status TEXT DEFAULT 'open', -- 'open', 'full', 'closed'
                created_at TEXT
            )
        """)
        # 임시 음성 채널 관리
        await db.execute("""
            CREATE TABLE IF NOT EXISTS temp_voice_channels (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER,
                owner_id INTEGER,
                is_locked INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        # 매너/경고 이력 (모더레이션)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                action_type TEXT, -- 'warn', 'timeout', 'kick', 'ban'
                created_at TEXT
            )
        """)
        # 서버 일별/시간별 스냅샷 통계
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                timestamp TEXT,
                member_count INTEGER,
                online_count INTEGER,
                voice_active_count INTEGER,
                top_games TEXT -- JSON object of game counts
            )
        """)
        await db.commit()

# DB 헬퍼 함수들
async def record_verification(user_id: int, birth_year: int):
    async with get_db() as db:
        await db.execute("""
            INSERT OR REPLACE INTO verified_users (user_id, birth_year, agreed_rules, verified_at)
            VALUES (?, ?, 1, ?)
        """, (user_id, birth_year, datetime.now().isoformat()))
        await db.commit()

async def is_user_verified(user_id: int) -> bool:
    async with get_db() as db:
        async with db.execute("SELECT 1 FROM verified_users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def create_party(guild_id: int, channel_id: int, leader_id: int, leader_name: str, game_name: str, title: str, max_members: int, voice_channel_id: int = None) -> int:
    initial_members = json.dumps([{"id": leader_id, "name": leader_name}])
    async with get_db() as db:
        cursor = await db.execute("""
            INSERT INTO parties (guild_id, channel_id, leader_id, leader_name, game_name, title, max_members, current_members, voice_channel_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
        """, (guild_id, channel_id, leader_id, leader_name, game_name, title, max_members, initial_members, voice_channel_id, datetime.now().isoformat()))
        await db.commit()
        return cursor.lastrowid

async def update_party_message(party_id: int, message_id: int):
    async with get_db() as db:
        await db.execute("UPDATE parties SET message_id = ? WHERE party_id = ?", (message_id, party_id))
        await db.commit()

async def get_party(party_id: int):
    async with get_db() as db:
        async with db.execute("SELECT * FROM parties WHERE party_id = ?", (party_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_party_members(party_id: int, members: list, status: str):
    async with get_db() as db:
        await db.execute("UPDATE parties SET current_members = ?, status = ? WHERE party_id = ?", (json.dumps(members), status, party_id))
        await db.commit()

async def close_party(party_id: int):
    async with get_db() as db:
        await db.execute("UPDATE parties SET status = 'closed' WHERE party_id = ?", (party_id,))
        await db.commit()

async def get_recent_parties(limit: int = 20):
    async with get_db() as db:
        async with db.execute("SELECT * FROM parties ORDER BY party_id DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def record_temp_voice(channel_id: int, guild_id: int, owner_id: int):
    async with get_db() as db:
        await db.execute("INSERT OR REPLACE INTO temp_voice_channels (channel_id, guild_id, owner_id, is_locked, created_at) VALUES (?, ?, ?, 0, ?)",
                         (channel_id, guild_id, owner_id, datetime.now().isoformat()))
        await db.commit()

async def remove_temp_voice(channel_id: int):
    async with get_db() as db:
        await db.execute("DELETE FROM temp_voice_channels WHERE channel_id = ?", (channel_id,))
        await db.commit()

async def get_temp_voice(channel_id: int):
    async with get_db() as db:
        async with db.execute("SELECT * FROM temp_voice_channels WHERE channel_id = ?", (channel_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def set_temp_voice_lock(channel_id: int, is_locked: bool):
    async with get_db() as db:
        await db.execute("UPDATE temp_voice_channels SET is_locked = ? WHERE channel_id = ?", (1 if is_locked else 0, channel_id))
        await db.commit()
