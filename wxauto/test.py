from __future__ import annotations

import sys
from pathlib import Path

# Ensure imports work when running this file from project root.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weixin_platform.api import (
    WeixinApiSession,
)


def main() -> None:
    print("=== API function invocation test ===")
    session = WeixinApiSession()

    try:
        # 1) login(step_mode=True): first get QR link, then get bool result.
        try:
            login_flow = session.login(step_mode=True)
            qr_link = next(login_flow)
            print(f"login(step_mode=True) first -> {qr_link}")
            login_ok = next(login_flow)
            print(f"login(step_mode=True) second -> {login_ok}")
        except Exception as exc:
            print(f"login(step_mode=True) raised: {exc}")

        # 2) start_listener()
        try:
            listener_status = session.start_listener("VERIFY-123456", timeout_s=120)
            print(f"start_listener() -> {listener_status}")
        except Exception as exc:
            print(f"start_listener() raised: {exc}")

        # 3) start_listener_process() alias
        try:
            listener_status_alias = session.start_listener_process("VERIFY-123456", timeout_s=120)
            print(f"start_listener_process() -> {listener_status_alias}")
        except Exception as exc:
            print(f"start_listener_process() raised: {exc}")

        # 4) sendmessage(text)
        try:
            send_status = session.sendmessage("测试消息：hello from test.py")
            print(f"sendmessage() -> {send_status}")
        except Exception as exc:
            print(f"sendmessage() raised: {exc}")

        # 5) examine_connection(verification_text, timeout_s)
        try:
            check_ok = session.examine_connection("VERIFY-654321", timeout_s=20)
            print(f"examine_connection() -> {check_ok}")
        except Exception as exc:
            print(f"examine_connection() raised: {exc}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
