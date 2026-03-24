from __future__ import annotations

import os
import time
from typing import Callable

from .api_client import TokenStore, WeixinApiClient
from .classifier import MessageClassifier
from .models import WeixinMessage
from .modules import ModuleRouter

MessageHandler = Callable[[WeixinMessage], None]


class WeixinPlatformService:
    TOKEN_EXPIRY_REMINDER_AFTER_MS = 22 * 60 * 60 * 1000
    TOKEN_EXPIRY_REMINDER_TEXT = "令牌即将过期，发送任意信息重新激活令牌"

    def __init__(self, client: WeixinApiClient, token_store: TokenStore) -> None:
        self.client = client
        self.token_store = token_store
        self.handlers: list[MessageHandler] = []
        self.classifier = MessageClassifier()
        self.module_router = ModuleRouter()
        self.active_user_id = self._normalize_weixin_user_id(self.token_store.load_active_user() or "")

    def add_message_handler(self, handler: MessageHandler) -> None:
        self.handlers.append(handler)

    @staticmethod
    def _normalize_weixin_user_id(user_id: str) -> str:
        clean = user_id.strip()
        if not clean:
            return clean
        if "@" in clean:
            return clean
        return f"{clean}@im.wechat"

    def send_text_message(self, text: str, context_token: str = "") -> None:
        target = self.active_user_id
        if not target:
            record = self.token_store.load_record() or {}
            candidate = str(record.get("user_id") or "").strip()
            target = self._normalize_weixin_user_id(candidate)
        if not target:
            raise RuntimeError("No active user found. Run 'run' and receive one message first.")
        self.client.send_text_message(to_user_id=target, text=text, context_token=context_token)

    def _allow_sender(self, sender_id: str) -> bool:
        if not self.active_user_id:
            self.active_user_id = sender_id
            self.token_store.bind_active_user(sender_id)
            print(f"[ACTIVE-USER-BOUND] user_id={sender_id}")
            return True

        if sender_id != self.active_user_id:
            print(
                f"[IGNORED] from={sender_id} reason=single_user_only "
                f"active_user={self.active_user_id}"
            )
            return False

        return True

    def _extract_text(self, message: WeixinMessage) -> str:
        texts: list[str] = []
        for item in message.item_list:
            if item.type == 1 and item.text_item and item.text_item.text:
                texts.append(item.text_item.text)
        return "\n".join(texts).strip()

    def _record_user_message_time(self, message: WeixinMessage) -> None:
        ts_ms = message.create_time_ms or int(time.time() * 1000)
        self.token_store.update_last_user_message_time_ms(ts_ms)

    def _resolve_target_user(self) -> str:
        target = self.active_user_id
        if target:
            return target
        record = self.token_store.load_record() or {}
        candidate = str(record.get("user_id") or "").strip()
        normalized = self._normalize_weixin_user_id(candidate)
        if normalized:
            return normalized
        return ""

    def _send_token_expiry_reminder_if_needed(self) -> None:
        last_ts = self.token_store.load_last_user_message_time_ms()
        if not last_ts:
            return
        if self.token_store.load_token_expiry_reminder_sent():
            return

        now_ms = int(time.time() * 1000)
        if now_ms - last_ts <= self.TOKEN_EXPIRY_REMINDER_AFTER_MS:
            return

        target = self._resolve_target_user()
        if not target:
            return

        resp = self.client.send_text_message(
            to_user_id=target,
            text=self.TOKEN_EXPIRY_REMINDER_TEXT,
            context_token="",
        )
        print(
            f"[TOKEN-EXPIRY-REMINDER] to={target} ret={resp.ret} "
            f"errcode={resp.errcode} errmsg={resp.errmsg}"
        )
        self.token_store.set_token_expiry_reminder_sent(True)

    def _default_message_handler(self, message: WeixinMessage) -> None:
        sender = message.from_user_id or "<unknown>"
        text = self._extract_text(message)
        print(
            f"[INCOMING] from={sender} message_id={message.message_id} "
            f"type={message.message_type} state={message.message_state} text={text}"
        )

        # Only auto-reply to user text messages.
        if message.message_type != 1:
            return
        if not text:
            return
        if not message.from_user_id:
            return
        sender_id = self._normalize_weixin_user_id(message.from_user_id)
        if not self._allow_sender(sender_id):
            return
        self._record_user_message_time(message)

        verify_text, verify_status = self.token_store.load_listener_verification()
        if verify_text and verify_status == "pending" and text.strip() == verify_text:
            self.token_store.set_listener_verification(verify_text=verify_text, status="success")
            print(f"[LISTENER-VERIFY] from={sender_id} status=success")

        if not message.context_token:
            print(f"[SKIP-REPLY] message_id={message.message_id} reason=missing_context_token")
            return

        category = self.classifier.classify(text)
        reply_text = self.module_router.route(category=category, message=message, text=text)
        print(f"[CLASSIFIED] message_id={message.message_id} category={category}")

        resp = self.client.send_text_message(
            to_user_id=sender_id,
            text=reply_text,
            context_token=message.context_token,
        )
        print(
            f"[REPLIED] to={sender_id} message_id={message.message_id} "
            f"ret={resp.ret} errcode={resp.errcode} errmsg={resp.errmsg}"
        )

    def run_forever(self) -> None:
        self.token_store.set_listener_state(started=True, pid=os.getpid())
        cursor = ""
        try:
            self._send_token_expiry_reminder_if_needed()
            while True:
                updates = self.client.get_updates(cursor)
                if updates.ret != 0:
                    raise RuntimeError(f"getupdates failed: errcode={updates.errcode}, errmsg={updates.errmsg}")

                if updates.get_updates_buf:
                    cursor = updates.get_updates_buf

                for msg in updates.msgs:
                    self._default_message_handler(msg)
                    for handler in self.handlers:
                        handler(msg)

                sleep_ms = updates.longpolling_timeout_ms or 0
                if sleep_ms > 0:
                    time.sleep(max(sleep_ms / 1000.0, 0.05))
        finally:
            self.token_store.set_listener_state(started=False)
