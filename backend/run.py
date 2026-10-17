import asyncio
import logging
import sys
import uvicorn
from config import DISCORD_TOKEN, API_HOST, API_PORT
from database import init_db
from bot.core.bot import bot_instance
from api.main import app

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("Launcher")

async def start_api():
    config = uvicorn.Config(app=app, host=API_HOST, port=API_PORT, log_level="warning")
    server = uvicorn.Server(config)
    logger.info(f"🌐 FastAPI Dashboard API running on http://{API_HOST}:{API_PORT}")
    await server.serve()

async def start_bot():
    if not DISCORD_TOKEN or DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.warning("⚠️ DISCORD_TOKEN이 설정되지 않았습니다. .env 파일에 토큰을 입력하면 봇이 자동으로 로그인됩니다.")
        logger.warning("ℹ️ 웹 대시보드 API는 현재 정상 동작 중이므로 대시보드를 먼저 둘러보실 수 있습니다.")
        return

    logger.info("🤖 Starting Discord Bot...")
    try:
        await bot_instance.start(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"❌ 봇 시작 실패: {e}")

async def main():
    logger.info("📦 Initializing Database...")
    await init_db()
    logger.info("✅ Database initialized.")

    await asyncio.gather(
        start_api(),
        start_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Server stopped.")
