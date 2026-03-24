from __future__ import annotations

from ..models import WeixinMessage


class DemoModule:
    """Example module used by the classifier router."""

    def handle(self, message: WeixinMessage, text: str) -> str:
        _ = message
        _ = text
        return "成功分类"
