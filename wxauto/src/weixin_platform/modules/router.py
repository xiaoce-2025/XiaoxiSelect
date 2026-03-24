from __future__ import annotations

from ..models import WeixinMessage
from .base import MessageModule
from .demo_module import DemoModule
from .weather_module import WeatherModule
from .yxx_module import YxxModule


class ModuleRouter:
    """Dispatch classified messages to corresponding modules."""

    def __init__(self) -> None:
        self._modules: dict[str, MessageModule] = {
            "demo": DemoModule(),
            "empty": DemoModule(),
            "unknown": DemoModule(),
            "weather": WeatherModule(),
            "yxx": YxxModule(),
        }

    def route(self, category: str, message: WeixinMessage, text: str) -> str:
        module = self._modules.get(category, self._modules["unknown"])
        return module.handle(message, text)

    def has_module(self, module_name: str) -> bool:
        return module_name in self._modules

    def list_modules(self) -> list[str]:
        return sorted(self._modules.keys())
