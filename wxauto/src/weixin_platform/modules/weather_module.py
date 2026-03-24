from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from ..models import WeixinMessage


class WeatherModule:
    """Weather module using fixed Haidian district weather API."""

    WEATHER_API_URL = "http://t.weather.itboy.net/api/weather/city/101010200"

    def handle(self, message: WeixinMessage, text: str) -> str:
        _ = message
        _ = text
        return self.fetch_today_weather_text()

    def fetch_today_weather_text(self) -> str:
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.WEATHER_API_URL)
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            return f"天气查询失败: {exc}"

        if not isinstance(payload, dict):
            return "天气查询失败: 返回格式异常"

        data = payload.get("data")
        city_info = payload.get("cityInfo")
        if not isinstance(data, dict) or not isinstance(city_info, dict):
            return "天气查询失败: 缺少 data/cityInfo 字段"

        forecast = data.get("forecast")
        if not isinstance(forecast, list) or not forecast:
            return "天气查询失败: forecast 为空"

        today = forecast[0]
        if not isinstance(today, dict):
            return "天气查询失败: 今日天气数据异常"

        city = str(city_info.get("city", "未知地区"))
        date_text = str(today.get("ymd") or payload.get("date") or datetime.now().strftime("%Y-%m-%d"))
        weather_type = str(today.get("type", "未知"))
        high = str(today.get("high", ""))
        low = str(today.get("low", ""))
        fx = str(today.get("fx", "未知风向"))
        fl = str(today.get("fl", "未知风力"))

        return (
            f"{city} {date_text} 天气: {weather_type}，{low}，{high}，"
            f"风向风力: {fx} {fl}"
        )
