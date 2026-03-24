from __future__ import annotations

from typing import Protocol

from ..models import WeixinMessage


class MessageModule(Protocol):
    """Contract for message modules."""

    def handle(self, message: WeixinMessage, text: str) -> str:
        """Handle a classified message and return text to send back."""
