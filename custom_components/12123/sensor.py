"""Home Assistant sensor platform entry point."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .data.coordinator import JiaoguanDataUpdateCoordinator
from .entities.category import JiaoguanCategorySensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[JiaoguanDataUpdateCoordinator],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create category sensors; details live in their attributes."""
    coordinator = entry.runtime_data
    registry = er.async_get(hass)
    keep_unique_ids = {
        f"{entry.entry_id}_driver",
        f"{entry.entry_id}_user_info",
        f"{entry.entry_id}_vehicles",
        f"{entry.entry_id}_violations",
        f"{entry.entry_id}_business_notices",
        f"{entry.entry_id}_service_reminders",
        f"{entry.entry_id}_status",
    }
    # Remove old score/per-vehicle entities from the registry so the
    # migration does not leave stale entries.
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.unique_id not in keep_unique_ids:
            registry.async_remove(entity.entity_id)

    entities = [
        JiaoguanCategorySensor(coordinator, entry, "driver", "驾驶证信息"),
        JiaoguanCategorySensor(coordinator, entry, "user_info", "用户信息"),
        JiaoguanCategorySensor(coordinator, entry, "vehicles", "车辆信息"),
        JiaoguanCategorySensor(coordinator, entry, "violations", "车辆违章"),
        JiaoguanCategorySensor(coordinator, entry, "business_notices", "业务告知"),
        JiaoguanCategorySensor(coordinator, entry, "service_reminders", "服务提醒"),
        JiaoguanCategorySensor(coordinator, entry, "status", "在线状态"),
    ]
    async_add_entities(entities)
