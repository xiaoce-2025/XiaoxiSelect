# Weixin Interface Platform (Python)

A standalone Python service for Weixin bot login, message receiving, classification, and message sending.

This project provides:
- QR code login (scan + confirm on phone).
- Login verification and token persistence.
- Long polling message receiver.
- Print all incoming text messages to terminal.
- Auto reply with module-classified response.
- Extensible classifier and module router.
- Proactive message sending API.
- Single active-user restriction (only one user can interact at a time).

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Configure

Create `.env`:

```env
WX_API_BASE_URL=https://ilinkai.weixin.qq.com/
WX_TOKEN_FILE=.weixin_token.json
WX_POLL_TIMEOUT_MS=35000
WX_QR_BOT_TYPE=3
WX_QR_WAIT_TIMEOUT_S=480
WX_QR_REFRESH_MAX=3
```

## 3. Login (QR scan)

```bash
PYTHONPATH=src python -m weixin_platform.cli login
```

Behavior:
- Program requests QR code from backend (`ilink/bot/get_bot_qrcode`).
- Terminal prints ASCII QR.
- You scan and confirm on phone.
- Program polls status (`ilink/bot/get_qrcode_status`) until confirmed.
- Returned token and account info are saved into token file.

Fallback (manual token login):

```bash
PYTHONPATH=src python -m weixin_platform.cli token-login --token "<your_token>"
```

## 4. Run bot loop

```bash
PYTHONPATH=src python -m weixin_platform.cli run
```

Behavior:
- Incoming user text is printed.
- Text is classified by `classifier.py` and handled by module router.
- Program replies with module output.
- First valid sender is bound as active user.
- Messages from any other user are ignored (single-user mode).

## 5. Proactively send message

```bash
PYTHONPATH=src python -m weixin_platform.cli send --text "hello"
```

Behavior:
- `send` only accepts text.
- Target user ID is resolved automatically from login state:
  - first from `active_user_id` (bound during runtime),
  - fallback to `user_id` stored at login.

## 6. Python API

File: `src/weixin_platform/api.py`

Recommended usage:

```python
from weixin_platform.api import WeixinApiSession

session = WeixinApiSession()  # starts a dedicated subprocess automatically
try:
  flow = session.login(step_mode=True)
  qr_link = next(flow)
  login_ok = next(flow)
  listener_ok = session.start_listener("VERIFY-123456", timeout_s=120)
  send_status = session.sendmessage("hello")
finally:
  session.close()  # stops and cleans subprocess
```

`WeixinApiSession` behavior:
- `__init__` starts one subprocess.
- Login/listen/send/examine actions are executed inside that subprocess.
- `close()`/object destruction shuts down the subprocess automatically.

- `login() -> str`
  - Clears existing login info first.
  - Triggers QR login initialization and returns QR content link/text.
- `sendmessage(text: str) -> str`
  - Sends text to the active user resolved from login info.
  - If listener process is not started, returns `请先启动监听进程`.
- `start_listener(verification_text: str, timeout_s: int = 120) -> bool`
  - Starts a background listener process.
  - Waits until user sends the exact `verification_text`.
  - Returns `True` on successful verification, else `False`.
  - Listener persists user last-message time and checks token inactivity.
  - On startup, if current time is more than 22 hours after last user message,
    it sends one-time reminder: `令牌即将过期，发送任意信息重新激活令牌`.
- `examine_connection(verification_text: str, timeout_s: int = 60) -> bool`
  - Sends a verification prompt to user.
  - Waits for user to send the exact verification text and returns whether matched in time.

## Project Structure

- `src/weixin_platform/config.py`: environment config loading.
- `src/weixin_platform/models.py`: API models.
- `src/weixin_platform/api_client.py`: HTTP API wrapper and token persistence.
- `src/weixin_platform/qr_login.py`: QR generation + scan status polling.
- `src/weixin_platform/service.py`: polling loop and message dispatch.
- `src/weixin_platform/classifier.py`: message classification entry.
- `src/weixin_platform/modules/`: classified message handler modules.
- `src/weixin_platform/cli.py`: command line entry (`login`, `token-login`, `run`, `send`).

## Classifier and Modules

Runtime flow:
- Receive text message.
- Classify in `src/weixin_platform/classifier.py`.
- Dispatch to module in `src/weixin_platform/modules/router.py`.
- Send module output as reply.

Current sample outputs:
- demo module: `成功分类`
- yxx module: `你好呀，我是严小希~`
- weather module: current weather text

You can add new module files under `src/weixin_platform/modules/` and extend the router mapping.
