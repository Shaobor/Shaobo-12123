"""Common Home Assistant device metadata for 12123 sensors."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..data.coordinator import JiaoguanDataUpdateCoordinator


class JiaoguanEntity(CoordinatorEntity[JiaoguanDataUpdateCoordinator], SensorEntity):
    """Base entity tied to one backend authorization."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JiaoguanDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        overview = (self.coordinator.data or {}).get("overview") or {}
        user_info = overview.get("user_info") or {}
        phone = str(user_info.get("sjhm") or "").strip()
        masked_phone = f"{phone[:3]}****{phone[-4:]}" if len(phone) >= 7 else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"12123({masked_phone})" if masked_phone else "12123",
            manufacturer="Shaobor",
            model="12123",
        )
