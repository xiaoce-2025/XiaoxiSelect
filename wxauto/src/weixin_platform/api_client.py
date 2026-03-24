from __future__ import annotations

import base64
import json
import os
import random
import uuid
from pathlib import Path
from typing import Any

import httpx

from .models import GenericResponse, GetUpdatesResponse


class TokenStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _write_record(self, record: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    def save(self, token: str) -> None:
        record = self.load_record() or {}
        record["token"] = token
        # New login token invalidates previous active conversation binding.
        record.pop("active_user_id", None)
        self._write_record(record)

    def save_record(self, record: dict[str, Any]) -> None:
        self._write_record(record)

    def load_record(self) -> dict[str, Any] | None:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            return None
        return None

    def load(self) -> str | None:
        data = self.load_record()
        if not data:
            return None
        token = data.get("token")
        if isinstance(token, str) and token:
            return token
        return None

    def bind_active_user(self, user_id: str) -> None:
        clean = user_id.strip()
        if not clean:
            return
        record = self.load_record() or {}
        record["active_user_id"] = clean
        self._write_record(record)

    def clear_active_user(self) -> None:
        record = self.load_record() or {}
        if "active_user_id" in record:
            record.pop("active_user_id", None)
            self._write_record(record)

    def load_active_user(self) -> str | None:
        data = self.load_record()
        if not data:
            return None
        active_user_id = data.get("active_user_id")
        if isinstance(active_user_id, str) and active_user_id.strip():
            return active_user_id.strip()
        return None

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def set_listener_state(self, started: bool, pid: int | None = None) -> None:
        record = self.load_record() or {}
        if started:
            record["listener_started"] = True
            if isinstance(pid, int) and pid > 0:
                record["listener_pid"] = pid
        else:
            record["listener_started"] = False
            record.pop("listener_pid", None)
        self._write_record(record)

    def is_listener_started(self) -> bool:
        record = self.load_record() or {}
        started = bool(record.get("listener_started"))
        pid_raw = record.get("listener_pid")
        pid = int(pid_raw) if isinstance(pid_raw, int) or (isinstance(pid_raw, str) and pid_raw.isdigit()) else 0
        if not started:
            return False
        if pid <= 0:
            return True
        alive = self._is_pid_alive(pid)
        if not alive:
            self.set_listener_state(started=False)
            return False
        return True

    def update_last_user_message_time_ms(self, timestamp_ms: int) -> None:
        if timestamp_ms <= 0:
            return
        record = self.load_record() or {}
        record["last_user_message_time_ms"] = int(timestamp_ms)
        # New user activity means token is active again.
        record["token_expiry_reminder_sent"] = False
        self._write_record(record)

    def load_last_user_message_time_ms(self) -> int | None:
        record = self.load_record() or {}
        value = record.get("last_user_message_time_ms")
        if isinstance(value, int) and value > 0:
            return value
        if isinstance(value, str) and value.isdigit():
            parsed = int(value)
            if parsed > 0:
                return parsed
        return None

    def set_token_expiry_reminder_sent(self, sent: bool) -> None:
        record = self.load_record() or {}
        record["token_expiry_reminder_sent"] = bool(sent)
        self._write_record(record)

    def load_token_expiry_reminder_sent(self) -> bool:
        record = self.load_record() or {}
        return bool(record.get("token_expiry_reminder_sent"))

    def set_listener_verification(self, verify_text: str, status: str) -> None:
        record = self.load_record() or {}
        record["listener_verify_text"] = verify_text
        record["listener_verify_status"] = status
        self._write_record(record)

    def load_listener_verification(self) -> tuple[str, str]:
        record = self.load_record() or {}
        verify_text = str(record.get("listener_verify_text") or "")
        status = str(record.get("listener_verify_status") or "")
        return verify_text, status


class WeixinApiClient:
    def __init__(self, base_url: str, token: str, timeout_s: float = 40.0) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.timeout_s = timeout_s

    @staticmethod
    def _gen_wechat_uin() -> str:
        value = random.randint(1, 2**32 - 1)
        return base64.b64encode(value.to_bytes(4, byteorder="big")).decode("ascii")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "Authorization": f"Bearer {self.token}",
            "X-WECHAT-UIN": self._gen_wechat_uin(),
        }

    @staticmethod
    def _base_info() -> dict[str, str]:
        # Keep channel_version explicit for compatibility with upstream expectations.
        return {"channel_version": "python-weixin-platform/0.1.0"}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self.base_url + path.lstrip("/")
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError(f"Unexpected response format from {url}")
            return data

    @staticmethod
    def _ensure_ret_ok(data: dict[str, Any], action: str) -> None:
        ret = data.get("ret")
        if ret is None or ret == 0:
            return
        raise RuntimeError(
            f"{action} failed: ret={ret}, errcode={data.get('errcode')}, errmsg={data.get('errmsg')}"
        )

    def _get(self, path: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        url = self.base_url + path.lstrip("/")
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(url, params=params or {}, headers=headers or {})
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError(f"Unexpected response format from {url}")
            return data

    def get_updates(self, cursor: str = "") -> GetUpdatesResponse:
        try:
            raw = self._post(
                "ilink/bot/getupdates",
                {"get_updates_buf": cursor, "base_info": self._base_info()},
            )
            self._ensure_ret_ok(raw, "getupdates")
            return GetUpdatesResponse.model_validate(raw)
        except httpx.ReadTimeout:
            # Long-poll timeout is expected; caller should continue polling.
            return GetUpdatesResponse(ret=0, msgs=[], get_updates_buf=cursor)

    def send_text_message(self, to_user_id: str, text: str, context_token: str = "") -> GenericResponse:
        client_id = f"python-weixin-{uuid.uuid4().hex[:16]}"
        payload = {
            "msg": {
                "from_user_id": "",
                "to_user_id": to_user_id,
                "client_id": client_id,
                "message_type": 2,
                "message_state": 2,
                "context_token": context_token,
                "item_list": [{"type": 1, "text_item": {"text": text}}],
            },
            "base_info": self._base_info(),
        }
        raw = self._post("ilink/bot/sendmessage", payload)
        self._ensure_ret_ok(raw, "sendmessage")
        return GenericResponse.model_validate(raw)

    def send_typing(self, ilink_user_id: str, typing_ticket: str, status: int) -> GenericResponse:
        raw = self._post(
            "ilink/bot/sendtyping",
            {
                "ilink_user_id": ilink_user_id,
                "typing_ticket": typing_ticket,
                "status": status,
                "base_info": self._base_info(),
            },
        )
        self._ensure_ret_ok(raw, "sendtyping")
        return GenericResponse.model_validate(raw)

    def get_config(self, ilink_user_id: str, context_token: str = "") -> GenericResponse:
        raw = self._post(
            "ilink/bot/getconfig",
            {
                "ilink_user_id": ilink_user_id,
                "context_token": context_token,
                "base_info": self._base_info(),
            },
        )
        self._ensure_ret_ok(raw, "getconfig")
        return GenericResponse.model_validate(raw)

    def verify_login(self) -> bool:
        resp = self.get_updates("")
        return resp.ret == 0

    def get_bot_qrcode(self, bot_type: str = "3") -> dict[str, Any]:
        return self._get(
            "ilink/bot/get_bot_qrcode",
            params={"bot_type": bot_type},
        )

    def get_qrcode_status(self, qrcode: str, timeout_s: float = 37.0) -> dict[str, Any]:
        headers = {"iLink-App-ClientVersion": "1"}
        url = self.base_url + "ilink/bot/get_qrcode_status"
        with httpx.Client(timeout=timeout_s) as client:
            response = client.get(url, params={"qrcode": qrcode}, headers=headers)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError(f"Unexpected response format from {url}")
            return data
