from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import qrcode

from .api_client import WeixinApiClient


@dataclass
class QrLoginResult:
    connected: bool
    token: str | None = None
    account_id: str | None = None
    user_id: str | None = None
    base_url: str | None = None
    message: str = ""


class QrLoginError(RuntimeError):
    pass


def render_qr_ascii(qr_content: str) -> str:
    qr = qrcode.QRCode(border=2)
    qr.add_data(qr_content)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    black = "██"
    white = "  "
    lines = [""]
    for row in matrix:
        lines.append("".join(black if cell else white for cell in row))
    lines.append("")
    return "\n".join(lines)


def login_with_qr(
    client: WeixinApiClient,
    bot_type: str = "3",
    wait_timeout_s: int = 480,
    refresh_max: int = 3,
) -> QrLoginResult:
    qr_resp = client.get_bot_qrcode(bot_type=bot_type)
    qrcode_id = str(qr_resp.get("qrcode") or "").strip()
    qrcode_content = str(qr_resp.get("qrcode_img_content") or "").strip()

    if not qrcode_id or not qrcode_content:
        raise QrLoginError(f"Failed to fetch QR code: {qr_resp}")

    print("请使用微信扫描下方二维码完成登录:\n")
    print(render_qr_ascii(qrcode_content))
    print(f"二维码内容: {qrcode_content}\n")

    deadline = time.time() + max(wait_timeout_s, 1)
    refresh_count = 1
    seen_scanned = False

    while time.time() < deadline:
        status_resp = client.get_qrcode_status(qrcode=qrcode_id, timeout_s=37.0)
        status = str(status_resp.get("status") or "wait").strip()

        if status == "wait":
            time.sleep(1)
            continue

        if status == "scaned":
            if not seen_scanned:
                print("已扫码，请在手机上确认授权...")
                seen_scanned = True
            time.sleep(1)
            continue

        if status == "expired":
            refresh_count += 1
            if refresh_count > max(refresh_max, 1):
                return QrLoginResult(connected=False, message="登录超时：二维码多次过期")

            print(f"二维码已过期，正在刷新 ({refresh_count}/{max(refresh_max, 1)})...")
            qr_resp = client.get_bot_qrcode(bot_type=bot_type)
            qrcode_id = str(qr_resp.get("qrcode") or "").strip()
            qrcode_content = str(qr_resp.get("qrcode_img_content") or "").strip()
            if not qrcode_id or not qrcode_content:
                return QrLoginResult(connected=False, message=f"刷新二维码失败: {qr_resp}")
            print(render_qr_ascii(qrcode_content))
            print(f"二维码内容: {qrcode_content}\n")
            seen_scanned = False
            time.sleep(1)
            continue

        if status == "confirmed":
            token = str(status_resp.get("bot_token") or "").strip() or None
            account_id = str(status_resp.get("ilink_bot_id") or "").strip() or None
            user_id = str(status_resp.get("ilink_user_id") or "").strip() or None
            base_url = str(status_resp.get("baseurl") or "").strip() or None
            if not token:
                return QrLoginResult(connected=False, message="登录已确认，但未返回 bot_token")
            if not account_id:
                return QrLoginResult(connected=False, message="登录已确认，但未返回 ilink_bot_id")
            return QrLoginResult(
                connected=True,
                token=token,
                account_id=account_id,
                user_id=user_id,
                base_url=base_url,
                message="登录成功",
            )

        return QrLoginResult(connected=False, message=f"未知二维码状态: {status_resp}")

    return QrLoginResult(connected=False, message="登录超时，请重试")
