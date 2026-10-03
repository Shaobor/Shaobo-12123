# -*- coding: utf-8 -*-
"""交管12123专属存储模块 (.storage/Shaobo_12123)"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "Shaobo_12123"


async def async_save_12123_account(
    hass: HomeAssistant,
    sfzmhm: str,
    account_data: dict[str, Any],
) -> None:
    """保存或更新交管12123凭据与数据到专属存储文件 (.storage/Shaobo_12123)"""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load() or {}
    existing = data.get(sfzmhm) or {}

    data[sfzmhm] = {
        **existing,
        **account_data,
        "sfzmhm": sfzmhm,
    }
    await store.async_save(data)
    _LOGGER.info("已将身份证 %s 的交管数据同步写入 .storage/%s", sfzmhm, STORAGE_KEY)


async def async_load_12123_accounts(hass: HomeAssistant) -> dict[str, Any]:
    """读取专属存储文件中的所有交管12123账号数据"""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    return await store.async_load() or {}


async def async_remove_12123_account(hass: HomeAssistant, sfzmhm: str) -> None:
    """从专属存储文件中移除指定身份证的账号"""
    store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    data = await store.async_load()
    if data and sfzmhm in data:
        data.pop(sfzmhm, None)
        await store.async_save(data)
        _LOGGER.info("已从 .storage/%s 中移除身份证 %s", STORAGE_KEY, sfzmhm)


class AuthorizationDraftStore:
    """兼顾授权草稿暂存，统一写入 Shaobo_12123 专属存储"""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)

    async def async_load(self) -> dict[str, Any] | None:
        data = await self._store.async_load()
        if isinstance(data, dict) and "draft_authorization_code" in data:
            return {"authorization_code": data["draft_authorization_code"]}
        return None

    async def async_save(self, authorization_code: str) -> None:
        data = await self._store.async_load() or {}
        data["draft_authorization_code"] = authorization_code
        await self._store.async_save(data)

    async def async_remove(self) -> None:
        data = await self._store.async_load() or {}
        if "draft_authorization_code" in data:
            data.pop("draft_authorization_code", None)
            await self._store.async_save(data)
