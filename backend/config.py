import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
GUILD_ID = int(os.getenv("GUILD_ID", 0)) if os.getenv("GUILD_ID", "0").isdigit() else None

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "bot_database.sqlite")

# 기본 지원 인기 게임 프리셋 (이모지 없이 깔끔한 텍스트 중심)
POPULAR_GAMES = [
    {"label": "리그 오브 레전드", "value": "lol", "description": "소환사의 협곡 / 칼바람 나락"},
    {"label": "발로란트", "value": "valorant", "description": "경쟁전 / 일반전 / 신속플레이"},
    {"label": "배틀그라운드", "value": "pubg", "description": "스쿼드 / 듀오 생존"},
    {"label": "오버워치 2", "value": "ow2", "description": "경쟁전 / 빠른 대전"},
    {"label": "로스트아크", "value": "lostark", "description": "레이드 / 군단장 파티"},
    {"label": "스팀 / 협동 / 인디", "value": "steam", "description": "팰월드, 헬다이버즈, 팩토리오 등"},
    {"label": "에이펙스 레전드", "value": "apex", "description": "트리오 / 랭크 매칭"},
    {"label": "기타 종합 게임", "value": "other", "description": "자유 종합 게임"}
]
