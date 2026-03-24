from __future__ import annotations

import httpx
import typer

from .api_client import TokenStore, WeixinApiClient
from .config import load_settings
from .qr_login import login_with_qr
from .service import WeixinPlatformService

app = typer.Typer(help="Independent Weixin interface platform (without OpenClaw)")



def _load_client(require_token: bool = True) -> WeixinApiClient:
    settings = load_settings()
    token_store = TokenStore(settings.token_file)
    token = token_store.load()

    if require_token and not token:
        raise typer.BadParameter(
            f"No token found. Run login first. token_file={settings.token_file}"
        )

    return WeixinApiClient(base_url=settings.api_base_url, token=token or "")


@app.command()
def login() -> None:
    """Login by scanning QR code and save returned bot token."""
    settings = load_settings()
    token_store = TokenStore(settings.token_file)
    if settings.token_file.exists():
        settings.token_file.unlink()
        print(f"Found existing login info, removed: {settings.token_file}")
    client = WeixinApiClient(base_url=settings.api_base_url, token="")

    try:
        result = login_with_qr(
            client=client,
            bot_type=settings.qr_bot_type,
            wait_timeout_s=settings.qr_wait_timeout_s,
            refresh_max=settings.qr_refresh_max,
        )
    except httpx.RequestError as exc:
        print("QR login failed: 无法连接到微信后端接口。")
        print(f"base_url={settings.api_base_url}")
        print(f"network_error={exc}")
        print("请检查 .env 中 WX_API_BASE_URL 是否可访问。")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        print(f"QR login failed: {exc}")
        raise typer.Exit(code=1) from exc

    if not result.connected or not result.token:
        print(f"QR login failed: {result.message}")
        raise typer.Exit(code=1)

    record = {
        "token": result.token,
        "account_id": result.account_id,
        "user_id": result.user_id,
        "base_url": result.base_url,
    }
    token_store.save_record(record)
    print(f"QR login succeeded. token saved at: {settings.token_file}")


@app.command("token-login")
def token_login(
    token: str | None = typer.Option(None, help="Existing bearer token from your backend auth"),
) -> None:
    """Fallback login: save token directly and verify by calling getupdates."""
    settings = load_settings()
    token_store = TokenStore(settings.token_file)

    input_token = token
    if not input_token:
        input_token = typer.prompt("Paste your bearer token")

    token_store.save(input_token)
    client = WeixinApiClient(base_url=settings.api_base_url, token=input_token)

    try:
        ok = client.verify_login()
    except httpx.RequestError as exc:
        print("Token login failed: 无法连接到微信后端接口。")
        print(f"base_url={settings.api_base_url}")
        print(f"network_error={exc}")
        print("请检查 .env 中 WX_API_BASE_URL 是否可访问。")
        raise typer.Exit(code=1) from exc

    if not ok:
        raise typer.Exit(code=1)

    print(f"Token login verification passed. token saved at: {settings.token_file}")


@app.command()
def run() -> None:
    """Start long-polling: print incoming messages and auto reply by module routing."""
    settings = load_settings()
    try:
        token_store = TokenStore(settings.token_file)
        client = _load_client(require_token=True)
        service = WeixinPlatformService(client=client, token_store=token_store)
        service.run_forever()
    except httpx.HTTPStatusError as exc:
        print("Run failed: 微信接口返回 HTTP 错误。")
        print(f"base_url={settings.api_base_url}")
        print(f"status={exc.response.status_code}")
        print(f"url={exc.request.url}")
        raise typer.Exit(code=1) from exc
    except httpx.RequestError as exc:
        print("Run failed: 无法连接到微信后端接口。")
        print(f"base_url={settings.api_base_url}")
        print(f"network_error={exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        print(f"Run failed: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def send(
    text: str = typer.Option(..., help="Text message"),
) -> None:
    """Proactively send a message to the active logged-in user."""
    settings = load_settings()
    client = _load_client(require_token=True)
    token_store = TokenStore(settings.token_file)
    service = WeixinPlatformService(client=client, token_store=token_store)
    service.send_text_message(text=text)
    print("Message sent.")


if __name__ == "__main__":
    app()
