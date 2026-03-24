from __future__ import annotations

import atexit
import os
from pathlib import Path
from queue import Empty
import threading
import time
import uuid
import multiprocessing as mp
from typing import Any, Iterator

import httpx

from .api_client import TokenStore, WeixinApiClient
from .classifier import MessageClassifier
from .config import load_settings
from .models import WeixinMessage
from .modules import ModuleRouter


TOKEN_EXPIRY_REMINDER_AFTER_MS = 22 * 60 * 60 * 1000
TOKEN_EXPIRY_REMINDER_TEXT = "令牌即将过期，发送任意信息重新激活令牌"


def _normalize_weixin_user_id(user_id: str) -> str:
    clean = str(user_id or "").strip()
    if not clean:
        return ""
    if "@" in clean:
        return clean
    return f"{clean}@im.wechat"


def _extract_text(message: WeixinMessage) -> str:
    texts: list[str] = []
    for item in message.item_list:
        if item.type == 1 and item.text_item and item.text_item.text:
            texts.append(item.text_item.text)
    return "\n".join(texts).strip()


def _resolve_target_user(token_store: TokenStore, active_user_id: str) -> str:
    normalized_active = _normalize_weixin_user_id(active_user_id)
    if normalized_active:
        return normalized_active
    record = token_store.load_record() or {}
    fallback_user = _normalize_weixin_user_id(str(record.get("user_id") or ""))
    if fallback_user:
        return fallback_user
    return ""


def _send_token_expiry_reminder_if_needed(
    client: WeixinApiClient,
    token_store: TokenStore,
    active_user_id: str,
) -> None:
    last_ts = token_store.load_last_user_message_time_ms()
    if not last_ts:
        return
    if token_store.load_token_expiry_reminder_sent():
        return

    now_ms = int(time.time() * 1000)
    if now_ms - last_ts <= TOKEN_EXPIRY_REMINDER_AFTER_MS:
        return

    target = _resolve_target_user(token_store, active_user_id)
    if not target:
        return

    client.send_text_message(to_user_id=target, text=TOKEN_EXPIRY_REMINDER_TEXT, context_token="")
    token_store.set_token_expiry_reminder_sent(True)


def _wait_for_login_result(
    client: WeixinApiClient,
    token_store: TokenStore,
    qrcode: str,
    qrcode_link: str,
    wait_timeout_s: int,
) -> bool:
    deadline = time.time() + max(int(wait_timeout_s), 1)

    while time.time() < deadline:
        status_resp = client.get_qrcode_status(qrcode=qrcode, timeout_s=37.0)
        status = str(status_resp.get("status") or "wait").strip()

        if status in {"wait", "scaned"}:
            time.sleep(1)
            continue

        if status == "confirmed":
            token = str(status_resp.get("bot_token") or "").strip()
            account_id = str(status_resp.get("ilink_bot_id") or "").strip()
            user_id = str(status_resp.get("ilink_user_id") or "").strip()
            base_url = str(status_resp.get("baseurl") or client.base_url).strip()
            if not token:
                return False

            token_store.save_record(
                {
                    "token": token,
                    "account_id": account_id,
                    "user_id": user_id,
                    "base_url": base_url,
                    "qrcode": qrcode,
                    "qrcode_link": qrcode_link,
                    "listener_started": False,
                    "listener_verify_text": "",
                    "listener_verify_status": "",
                }
            )
            return True

        if status in {"expired", "cancelled", "rejected"}:
            return False

        time.sleep(1)

    return False


def _listener_loop(
    stop_event: threading.Event,
    state: dict[str, Any],
    verify_lock: threading.Lock,
) -> None:
    token_store: TokenStore = state["token_store"]
    client: WeixinApiClient = state["client"]

    classifier = MessageClassifier()
    module_router = ModuleRouter()
    _send_token_expiry_reminder_if_needed(client, token_store, str(state.get("active_user_id") or ""))

    cursor = ""
    while not stop_event.is_set():
        updates = client.get_updates(cursor)
        if updates.get_updates_buf:
            cursor = updates.get_updates_buf

        for msg in updates.msgs:
            if msg.message_type != 1:
                continue
            if not msg.from_user_id:
                continue

            text = _extract_text(msg)
            if not text:
                continue

            sender_id = _normalize_weixin_user_id(msg.from_user_id)
            active_user_id = _normalize_weixin_user_id(str(state.get("active_user_id") or ""))
            if not active_user_id:
                state["active_user_id"] = sender_id
                token_store.bind_active_user(sender_id)
                active_user_id = sender_id
            if sender_id != active_user_id:
                continue

            ts_ms = msg.create_time_ms or int(time.time() * 1000)
            token_store.update_last_user_message_time_ms(ts_ms)

            with verify_lock:
                verify_text = str(state.get("verify_text") or "")
                verify_status = str(state.get("verify_status") or "")
                if verify_text and verify_status == "pending" and text.strip() == verify_text:
                    state["verify_status"] = "success"
                    token_store.set_listener_verification(verify_text=verify_text, status="success")
                    # Verification messages are consumed here and should not be routed.
                    continue

            if not msg.context_token:
                continue

            category = classifier.classify(text)
            reply_text = module_router.route(category=category, message=msg, text=text)
            client.send_text_message(
                to_user_id=sender_id,
                text=reply_text,
                context_token=msg.context_token,
            )

        sleep_ms = updates.longpolling_timeout_ms or 0
        if sleep_ms > 0:
            time.sleep(max(sleep_ms / 1000.0, 0.05))
        else:
            time.sleep(0.2)


def _worker_main(command_queue: mp.Queue, response_queue: mp.Queue) -> None:
    settings = load_settings()
    token_store = TokenStore(settings.token_file)

    state: dict[str, Any] = {
        "active_user_id": _normalize_weixin_user_id(token_store.load_active_user() or ""),
        "token_store": token_store,
        "client": None,
        "listener_thread": None,
        "listener_stop": None,
        "verify_text": "",
        "verify_status": "",
    }
    verify_lock = threading.Lock()

    def build_client_from_store() -> WeixinApiClient | None:
        token = token_store.load()
        if not token:
            return None
        return WeixinApiClient(base_url=settings.api_base_url, token=token)

    def is_listener_alive() -> bool:
        thread = state.get("listener_thread")
        return bool(thread and isinstance(thread, threading.Thread) and thread.is_alive())

    def ensure_listener_started() -> bool:
        if is_listener_alive():
            return True
        client = build_client_from_store()
        if not client:
            return False
        state["client"] = client
        stop_event = threading.Event()
        listener_thread = threading.Thread(
            target=_listener_loop,
            args=(stop_event, state, verify_lock),
            name="weixin-listener-thread",
            daemon=True,
        )
        state["listener_stop"] = stop_event
        state["listener_thread"] = listener_thread
        token_store.set_listener_state(started=True, pid=os.getpid())
        listener_thread.start()
        return True

    def stop_listener() -> None:
        stop_event = state.get("listener_stop")
        thread = state.get("listener_thread")
        if isinstance(stop_event, threading.Event):
            stop_event.set()
        if isinstance(thread, threading.Thread):
            thread.join(timeout=3)
        state["listener_stop"] = None
        state["listener_thread"] = None
        token_store.set_listener_state(started=False)

    while True:
        cmd = command_queue.get()
        req_id = cmd.get("id")
        action = str(cmd.get("action") or "")
        payload = cmd.get("payload") or {}

        def ok(result: Any) -> None:
            response_queue.put({"id": req_id, "ok": True, "result": result})

        def fail(error: str) -> None:
            response_queue.put({"id": req_id, "ok": False, "error": error})

        try:
            if action == "shutdown":
                stop_listener()
                ok(True)
                break

            if action == "login_start":
                if settings.token_file.exists():
                    settings.token_file.unlink()

                client = WeixinApiClient(base_url=settings.api_base_url, token="", timeout_s=80.0)

                resp: dict[str, Any] | None = None
                last_err: Exception | None = None
                for _ in range(3):
                    try:
                        resp = client.get_bot_qrcode(bot_type=settings.qr_bot_type)
                        break
                    except httpx.RequestError as exc:
                        last_err = exc
                        time.sleep(1.5)

                if resp is None:
                    fail(
                        "QR login failed: unable to reach backend. "
                        f"base_url={settings.api_base_url} "
                        f"network_error={last_err}"
                    )
                    continue

                qrcode = str(resp.get("qrcode") or "").strip()
                qrcode_link = str(resp.get("qrcode_img_content") or "").strip()
                if not qrcode or not qrcode_link:
                    fail(f"Failed to fetch QR code: {resp}")
                    continue

                token_store.save_record(
                    {
                        "qrcode": qrcode,
                        "qrcode_link": qrcode_link,
                        "base_url": settings.api_base_url,
                        "listener_started": False,
                        "listener_verify_text": "",
                        "listener_verify_status": "",
                    }
                )
                state["qrcode"] = qrcode
                state["qrcode_link"] = qrcode_link
                ok(qrcode_link)
                continue

            if action == "login_confirm":
                qrcode = str(state.get("qrcode") or "")
                qrcode_link = str(state.get("qrcode_link") or "")
                if not qrcode or not qrcode_link:
                    fail("No pending QR login. Call login_start first.")
                    continue
                wait_timeout_s = int(payload.get("wait_timeout_s") or settings.qr_wait_timeout_s)
                client = WeixinApiClient(base_url=settings.api_base_url, token="")
                login_ok = _wait_for_login_result(
                    client=client,
                    token_store=token_store,
                    qrcode=qrcode,
                    qrcode_link=qrcode_link,
                    wait_timeout_s=wait_timeout_s,
                )
                ok(bool(login_ok))
                continue

            if action == "start_listener":
                verification_text = str(payload.get("verification_text") or "").strip()
                timeout_s = int(payload.get("timeout_s") or 120)
                if not verification_text:
                    ok(False)
                    continue

                started = ensure_listener_started()
                if not started:
                    ok(False)
                    continue

                with verify_lock:
                    state["verify_text"] = verification_text
                    state["verify_status"] = "pending"
                    token_store.set_listener_verification(verify_text=verification_text, status="pending")

                token = token_store.load()
                target_user_id = _resolve_target_user(token_store, str(state.get("active_user_id") or ""))
                if token and target_user_id:
                    try:
                        client = build_client_from_store()
                        if client:
                            prompt = f"监听验证：请发送以下验证信息：{verification_text}"
                            client.send_text_message(to_user_id=target_user_id, text=prompt, context_token="")
                    except Exception:
                        pass

                deadline = time.time() + max(timeout_s, 1)
                while time.time() < deadline:
                    with verify_lock:
                        status = str(state.get("verify_status") or "")
                    if status == "success":
                        ok(True)
                        break
                    if not is_listener_alive():
                        ok(False)
                        break
                    time.sleep(1)
                else:
                    ok(False)
                continue

            if action == "start_listener_silent":
                started = ensure_listener_started()
                ok(bool(started))
                continue

            if action == "sendmessage":
                if not is_listener_alive():
                    ok("请先启动监听进程")
                    continue

                text = str(payload.get("text") or "")
                client = build_client_from_store()
                if not client:
                    ok("No token found. Complete login confirmation first.")
                    continue

                target_user_id = _resolve_target_user(token_store, str(state.get("active_user_id") or ""))
                if not target_user_id:
                    fail("No target user found in login info. Run listener and receive one message first.")
                    continue

                client.send_text_message(to_user_id=target_user_id, text=text, context_token="")
                ok("发送成功")
                continue

            if action == "examine_connection":
                verification_text = str(payload.get("verification_text") or "").strip()
                timeout_s = int(payload.get("timeout_s") or 60)
                if not verification_text:
                    fail("verification_text cannot be empty")
                    continue

                started = ensure_listener_started()
                if not started:
                    ok(False)
                    continue

                with verify_lock:
                    state["verify_text"] = verification_text
                    state["verify_status"] = "pending"
                    token_store.set_listener_verification(verify_text=verification_text, status="pending")

                token = token_store.load()
                target_user_id = _resolve_target_user(token_store, str(state.get("active_user_id") or ""))
                if token and target_user_id:
                    try:
                        client = build_client_from_store()
                        if client:
                            prompt = f"连接校验：请回复以下验证码：{verification_text}"
                            client.send_text_message(to_user_id=target_user_id, text=prompt, context_token="")
                    except Exception:
                        pass

                deadline = time.time() + max(timeout_s, 1)
                while time.time() < deadline:
                    with verify_lock:
                        status = str(state.get("verify_status") or "")
                    if status == "success":
                        ok(True)
                        break
                    if not is_listener_alive():
                        ok(False)
                        break
                    time.sleep(1)
                else:
                    ok(False)
                continue

            fail(f"Unknown action: {action}")
        except Exception as exc:
            fail(str(exc))


class WeixinApiSession:
    """Class-based API manager backed by one dedicated subprocess."""

    def __init__(self) -> None:
        ctx = mp.get_context("spawn")
        self._command_queue: mp.Queue = ctx.Queue()
        self._response_queue: mp.Queue = ctx.Queue()
        self._process = ctx.Process(
            target=_worker_main,
            args=(self._command_queue, self._response_queue),
            name="weixin-api-session-worker",
            daemon=True,
        )
        self._closed = False
        self._process.start()
        atexit.register(self.close)

    def _request(self, action: str, payload: dict[str, Any] | None = None, timeout_s: int = 300) -> Any:
        if self._closed:
            raise RuntimeError("Session already closed")

        req_id = uuid.uuid4().hex
        self._command_queue.put({"id": req_id, "action": action, "payload": payload or {}})

        deadline = time.time() + max(int(timeout_s), 1)
        while time.time() < deadline:
            remaining = max(deadline - time.time(), 0.1)
            try:
                resp = self._response_queue.get(timeout=remaining)
            except Empty:
                continue
            if resp.get("id") != req_id:
                continue
            if bool(resp.get("ok")):
                return resp.get("result")
            raise RuntimeError(str(resp.get("error") or "Unknown worker error"))

        raise TimeoutError(f"Request timeout: {action}")

    def login(self, step_mode: bool = False, wait_timeout_s: int | None = None) -> str | Iterator[str | bool]:
        qr_link = str(self._request("login_start", {}, timeout_s=60))
        timeout_s = wait_timeout_s if wait_timeout_s is not None else load_settings().qr_wait_timeout_s

        if not step_mode:
            return qr_link

        def _iter() -> Iterator[str | bool]:
            yield qr_link
            confirmed = bool(self._request("login_confirm", {"wait_timeout_s": int(timeout_s)}, timeout_s=int(timeout_s) + 30))
            yield confirmed

        return _iter()

    def start_listener(self, verification_text: str, timeout_s: int = 120) -> bool:
        return bool(
            self._request(
                "start_listener",
                {"verification_text": verification_text, "timeout_s": int(timeout_s)},
                timeout_s=int(timeout_s) + 30,
            )
        )

    def start_listener_silent(self) -> bool:
        return bool(self._request("start_listener_silent", {}, timeout_s=10))

    def start_listener_process(self, verification_text: str, timeout_s: int = 120) -> bool:
        return self.start_listener(verification_text=verification_text, timeout_s=timeout_s)

    def sendmessage(self, text: str) -> str:
        return str(self._request("sendmessage", {"text": text}, timeout_s=60))

    def examine_connection(self, verification_text: str, timeout_s: int = 60) -> bool:
        return bool(
            self._request(
                "examine_connection",
                {"verification_text": verification_text, "timeout_s": int(timeout_s)},
                timeout_s=int(timeout_s) + 30,
            )
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._request("shutdown", {}, timeout_s=10)
        except Exception:
            pass
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=3)

    def __enter__(self) -> "WeixinApiSession":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


_default_session: WeixinApiSession | None = None


def _get_default_session() -> WeixinApiSession:
    global _default_session
    if _default_session is None:
        _default_session = WeixinApiSession()
    return _default_session


def login(step_mode: bool = False, wait_timeout_s: int | None = None) -> str | Iterator[str | bool]:
    return _get_default_session().login(step_mode=step_mode, wait_timeout_s=wait_timeout_s)


def start_listener(verification_text: str, timeout_s: int = 120) -> bool:
    return _get_default_session().start_listener(verification_text=verification_text, timeout_s=timeout_s)


def start_listener_silent() -> bool:
    return _get_default_session().start_listener_silent()


def start_listener_process(verification_text: str, timeout_s: int = 120) -> bool:
    return _get_default_session().start_listener_process(verification_text=verification_text, timeout_s=timeout_s)


def sendmessage(text: str) -> str:
    return _get_default_session().sendmessage(text=text)


def examine_connection(verification_text: str, timeout_s: int = 60) -> bool:
    return _get_default_session().examine_connection(verification_text=verification_text, timeout_s=timeout_s)
