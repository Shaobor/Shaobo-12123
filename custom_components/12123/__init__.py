"""Set up the 12123 custom integration."""

from __future__ import annotations

import asyncio
import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

from .client.api import JiaoguanApiClient
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_AUTHORIZATION_CODE,
    CONF_BACKEND_URL,
    CONF_SFZMHM,
    CONF_SFZMHM_FULL,
    DEFAULT_BACKEND_URL,
    DOMAIN,
    PLATFORMS,
    SERVICE_REFRESH_VIOLATIONS,
    VERSION,
)
from .data.coordinator import JiaoguanDataUpdateCoordinator
from .storage import (
    AuthorizationDraftStore,
    async_remove_12123_account,
    async_save_12123_account,
)

JiaoguanConfigEntry = ConfigEntry[JiaoguanDataUpdateCoordinator]

_LOGGER = logging.getLogger(__name__)
_CARD_URL = f"/{DOMAIN}/12123-card.js"
_CARD_VERSION = VERSION




async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Register the custom card once in Lovelace resources when storage mode is enabled."""
    try:
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None) if lovelace else None
        if not resources or not hasattr(resources, "async_create_item"):
            return
        await resources.async_get_info()
        base_url = url.split("?")[0]
        matching = []
        for item in resources.async_items():
            item_url = item.get("url", "") if isinstance(item, dict) else getattr(item, "url", "")
            item_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
            if item_id and item_url.split("?")[0] == base_url:
                matching.append((item_id, item_url))
        if not matching:
            await resources.async_create_item({"res_type": "module", "url": url})
            _LOGGER.info("已自动将 12123 前端卡片注册到 Lovelace Resources: %s", url)
            return
        # 保留最新版本，清掉因版本号变化产生的重复资源。
        matching.sort(key=lambda pair: pair[1] != url)
        keep_id, keep_url = matching[0]
        for item_id, item_url in matching[1:]:
            await resources.async_delete_item(item_id)
            _LOGGER.debug("已移除重复的 12123 卡片资源: %s", item_url)
        if keep_url != url:
            await resources.async_update_item(keep_id, {"res_type": "module", "url": url})
    except Exception as err:  # 资源登记失败不应阻止集成加载
        _LOGGER.debug("自动注册 12123 Lovelace Resource 失败(可手动添加): %s", err)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the card's static files and Lovelace module resource."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    if os.path.isdir(frontend_dir) and not domain_data.get("static_paths_registered"):
        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig(f"/{DOMAIN}", frontend_dir, cache_headers=False),
                StaticPathConfig("/12123", frontend_dir, cache_headers=False),
            ])
            domain_data["static_paths_registered"] = True
            _LOGGER.info("已注册 12123 前端卡片资源路径: /%s -> %s", DOMAIN, frontend_dir)
        except Exception as err:
            _LOGGER.warning("注册 12123 前端卡片资源路径失败: %s", err)
    violation_image_dir = hass.config.path("www", "12123")
    os.makedirs(violation_image_dir, exist_ok=True)

    if not domain_data.get("violation_image_static_path_registered"):
        try:
            await hass.http.async_register_static_paths([
                StaticPathConfig("/12123-images", violation_image_dir, cache_headers=True)
            ])
            domain_data["violation_image_static_path_registered"] = True
            _LOGGER.info("已注册 12123 违章图片路径: /12123-images -> %s", violation_image_dir)

        except Exception as err:
            _LOGGER.warning("注册 12123 违章图片路径失败: %s", err)
    await _async_register_lovelace_resource(hass, f"{_CARD_URL}?v={_CARD_VERSION}")
    if not domain_data.get("refresh_service_registered"):
        async def _handle_refresh(call: ServiceCall) -> None:
            await _async_refresh_violations(hass, call)

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_VIOLATIONS,
            _handle_refresh,
        )
        domain_data["refresh_service_registered"] = True
    return True


async def _async_refresh_violations(hass: HomeAssistant, call: ServiceCall) -> None:
    """Force an immediate violation/photo refresh for one or all entries."""
    requested_entities = call.data.get("entity_id")
    if isinstance(requested_entities, str):
        requested_entities = [requested_entities]
    requested_entities = requested_entities or []

    target_entry_ids: set[str] = set()
    if requested_entities:
        registry = er.async_get(hass)
        for entity_id in requested_entities:
            registered = registry.async_get(entity_id)
            if registered and registered.config_entry_id:
                target_entry_ids.add(registered.config_entry_id)

    refresh_tasks = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if target_entry_ids and entry.entry_id not in target_entry_ids:
            continue
        coordinator = entry.runtime_data
        if coordinator is None:
            continue
        coordinator.async_force_violation_refresh()
        refresh_tasks.append(coordinator.async_request_refresh())
    if refresh_tasks:
        await asyncio.gather(*refresh_tasks)


async def _async_update_listener(hass: HomeAssistant, entry: JiaoguanConfigEntry) -> None:
    """Reload the coordinator after the polling option changes."""
    await hass.config_entries.async_reload(entry.entry_id)


def _mask_phone(value: object) -> str | None:
    """Return a short, non-identifying display form for a mobile number."""
    phone = str(value or "").strip()
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return None


def _mask_id_card(value: object) -> str | None:
    """Return a masked ID-card display value, masking full IDs defensively."""
    id_card = str(value or "").strip()
    if len(id_card) >= 10 and "*" not in id_card:
        return f"{id_card[:6]}********{id_card[-4:]}"
    return id_card or None


def _update_entry_title(
    hass: HomeAssistant,
    entry: JiaoguanConfigEntry,
    coordinator: JiaoguanDataUpdateCoordinator,
) -> None:
    """Name the entry after the current account without exposing raw PII."""
    overview = coordinator.data.get("overview", {})
    user_info = overview.get("user_info") or {}
    identity = _mask_id_card(user_info.get("sfzmhm")) or _mask_phone(user_info.get("sjhm"))
    if identity:
        if entry.title != identity:
            hass.config_entries.async_update_entry(entry, title=identity)


async def async_setup_entry(hass: HomeAssistant, entry: JiaoguanConfigEntry) -> bool:
    """Set up a configured relay connection."""
    client = JiaoguanApiClient(
        async_get_clientsession(hass),
        entry.data.get(CONF_BACKEND_URL, DEFAULT_BACKEND_URL),
        entry.data.get(CONF_ACCESS_TOKEN),
        entry.data.get(CONF_SFZMHM_FULL) or entry.data.get(CONF_SFZMHM),
    )
    coordinator = JiaoguanDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    _update_entry_title(hass, entry, coordinator)

    # 同步持久化写入专属存储 .storage/Shaobo_12123
    sfzmhm = entry.data.get(CONF_SFZMHM_FULL) or entry.data.get(CONF_SFZMHM)
    if sfzmhm:
        await async_save_12123_account(hass, sfzmhm, {
            CONF_AUTHORIZATION_CODE: entry.data.get(CONF_AUTHORIZATION_CODE),
            CONF_ACCESS_TOKEN: entry.data.get(CONF_ACCESS_TOKEN),
            CONF_BACKEND_URL: entry.data.get(CONF_BACKEND_URL),
            "title": entry.title,
            "metrics": coordinator.data.get("overview") if isinstance(coordinator.data, dict) else {},
        })

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: JiaoguanConfigEntry) -> bool:
    """Unload platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: JiaoguanConfigEntry) -> None:
    """Remove the saved authorization draft and account storage when the integration is deleted."""
    sfzmhm = entry.data.get(CONF_SFZMHM_FULL) or entry.data.get(CONF_SFZMHM)
    if sfzmhm:
        await async_remove_12123_account(hass, sfzmhm)

    other_entries = [
        item for item in hass.config_entries.async_entries(DOMAIN)
        if item.entry_id != entry.entry_id
    ]
    if not other_entries:
        await AuthorizationDraftStore(hass).async_remove()
