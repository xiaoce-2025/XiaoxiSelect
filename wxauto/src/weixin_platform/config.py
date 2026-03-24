from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass
class Settings:
    api_base_url: str
    token_file: Path
    poll_timeout_ms: int = 35000
    qr_bot_type: str = "3"
    qr_wait_timeout_s: int = 480
    qr_refresh_max: int = 3



def load_settings() -> Settings:
    load_dotenv()
    api_base_url = os.getenv("WX_API_BASE_URL", "https://ilinkai.weixin.qq.com/").strip()
    token_file = Path(os.getenv("WX_TOKEN_FILE", ".weixin_token.json")).resolve()
    poll_timeout_ms = int(os.getenv("WX_POLL_TIMEOUT_MS", "35000"))
    qr_bot_type = os.getenv("WX_QR_BOT_TYPE", "3").strip() or "3"
    qr_wait_timeout_s = int(os.getenv("WX_QR_WAIT_TIMEOUT_S", "480"))
    qr_refresh_max = int(os.getenv("WX_QR_REFRESH_MAX", "3"))
    return Settings(
        api_base_url=api_base_url,
        token_file=token_file,
        poll_timeout_ms=poll_timeout_ms,
        qr_bot_type=qr_bot_type,
        qr_wait_timeout_s=qr_wait_timeout_s,
        qr_refresh_max=qr_refresh_max,
    )
