from __future__ import annotations

from ..models import WeixinMessage


class YxxModule:
    """Example module used by the classifier router."""

    def handle(self, message: WeixinMessage, text: str) -> str:
        _ = message
        _ = text
        return "你好呀，我是严小希~"
