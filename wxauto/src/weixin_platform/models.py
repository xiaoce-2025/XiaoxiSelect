from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TextItem(BaseModel):
    text: str = ""


class MessageItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: int
    text_item: TextItem | None = None


class WeixinMessage(BaseModel):
    model_config = ConfigDict(extra="allow")

    seq: int | None = None
    message_id: int | None = None
    from_user_id: str | None = None
    to_user_id: str | None = None
    create_time_ms: int | None = None
    session_id: str | None = None
    message_type: int | None = None
    message_state: int | None = None
    context_token: str | None = None
    item_list: list[MessageItem] = Field(default_factory=list)


class GetUpdatesResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    ret: int = 0
    errcode: int | None = None
    errmsg: str | None = None
    msgs: list[WeixinMessage] = Field(default_factory=list)
    get_updates_buf: str = ""
    longpolling_timeout_ms: int | None = None


class GenericResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    ret: int = 0
    errcode: int | None = None
    errmsg: str | None = None
    data: dict[str, Any] | None = None
