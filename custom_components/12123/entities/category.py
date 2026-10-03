"""The top-level 12123 category sensors."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlsplit

from homeassistant.config_entries import ConfigEntry

from ..data.coordinator import JiaoguanDataUpdateCoordinator
from .base import JiaoguanEntity


class JiaoguanCategorySensor(JiaoguanEntity):
    """Expose one 12123 category as a sensor and keep its details in attributes."""

    def __init__(
        self,
        coordinator: JiaoguanDataUpdateCoordinator,
        entry: ConfigEntry,
        category: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self._category = category
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{category}"

        if category == "driver":
            self._attr_icon = "mdi:card-account-details"
            self._attr_native_unit_of_measurement = "分"
        elif category == "vehicles":
            self._attr_icon = "mdi:car-multiple"
            self._attr_native_unit_of_measurement = "辆"
        elif category == "violations":
            self._attr_icon = "mdi:alert-circle"
            self._attr_native_unit_of_measurement = "起"
        elif category == "business_notices":
            self._attr_icon = "mdi:clipboard-text"
            self._attr_native_unit_of_measurement = "条"
        elif category == "user_info":
            self._attr_icon = "mdi:account"
            self._attr_native_unit_of_measurement = None
        elif category == "status":
            self._attr_icon = "mdi:lan-connect"
            self._attr_native_unit_of_measurement = None
        else:
            self._attr_icon = "mdi:message-text"
            self._attr_native_unit_of_measurement = "条"

    @property
    def native_value(self) -> int | str:
        """Return the category's primary count/value."""
        if self._category == "status":
            return "在线" if self.coordinator.last_update_success else "离线"

        overview = self.coordinator.data.get("overview", {})

        if self._category == "user_info":
            user_info = overview.get("user_info") or {}
            return _mask_person_name(user_info.get("xm")) or "未知"
        if self._category == "driver":
            return self._as_int((overview.get("driver_info") or {}).get("ljjf"))
        if self._category == "vehicles":
            return len(overview.get("vehicle_list") or [])
        if self._category == "violations":
            violations = self.coordinator.data.get("violations", {})
            total = violations.get("total_violations")
            if total is not None:
                return self._as_int(total)
            return sum(
                self._as_int(item.get("violation_count"))
                for item in violations.get("data") or []
                if isinstance(item, dict)
            )
        messages = self.coordinator.data.get(self._category, {})
        total = messages.get("total")
        if total is not None:
            return self._as_int(total)
        return self._as_int(messages.get("count")) or len(messages.get("data") or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Keep detail data under its category instead of creating extra entities."""
        if self._category == "status":
            last_exception = getattr(self.coordinator, "last_exception", None)
            return {
                "后端状态": self.native_value,
                "最近一次更新成功": self.coordinator.last_update_success,
                "最近一次错误": str(last_exception) if last_exception else None,
                "数据更新时间": (
                    self.coordinator.last_data_update.isoformat()
                    if self.coordinator.last_data_update
                    else None
                ),
                "数据刷新间隔": self.coordinator.scan_interval_minutes,
                "违章信息刷新间隔": self.coordinator.violation_scan_interval_minutes,
                "消息中心刷新间隔": self.coordinator.message_scan_interval_minutes,
                "凭证": "固定服务Token + 身份证校验",
            }

        overview = self.coordinator.data.get("overview", {})

        if self._category == "user_info":
            user_info = dict(overview.get("user_info") or {})
            if "xm" in user_info:
                user_info["xm"] = _mask_person_name(user_info.get("xm"))
            return {"user_info": user_info}
        if self._category == "driver":
            return {
                "driver_info": overview.get("driver_info") or {},
            }
        if self._category == "vehicles":
            vehicles = overview.get("vehicle_list") or []
            return {"vehicle_count": len(vehicles), "vehicles": vehicles}
        if self._category == "violations":
            violations = self.coordinator.data.get("violations", {})
            return {
                "total_violations": self.native_value,
                "summary": overview.get("violations_summary") or {},
                "vehicle_violations": [
                    _normalize_violation_item(item)
                    for item in (violations.get("data") or [])
                ],
            }
        messages = self.coordinator.data.get(self._category, {})
        return {
            "message_count": self.native_value,
            "category": messages.get("category"),
            "category_desc": messages.get("category_desc"),
            "messages": messages.get("data") or [],
        }

    @property
    def available(self) -> bool:
        """Keep the status entity visible so it can report an offline state."""
        if self._category == "status":
            return True
        return super().available

    @staticmethod
    def _as_int(value: Any) -> int:
        """Convert API numeric strings without allowing malformed values to break updates."""
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


def _normalize_violation_item(item: Any) -> Any:
    """Remove malformed official photo placeholders from violation attributes."""
    if not isinstance(item, dict):
        return item

    normalized = dict(item)
    if "photos" in normalized:
        normalized["photos"] = _valid_photo_urls(normalized["photos"])
    if "local_photos" in normalized:
        normalized["local_photos"] = _valid_local_photo_urls(normalized["local_photos"])

    nested = normalized.get("violations")
    if isinstance(nested, list):
        normalized["violations"] = [
            _normalize_violation_item(violation) for violation in nested
        ]
    return normalized


def _mask_person_name(value: Any) -> str:
    """Mask the surname while keeping the remaining given name visible."""
    name = str(value or "").strip()
    if not name:
        return ""
    if name.startswith("*"):
        return name
    return "*" if len(name) == 1 else f"*{name[1:]}"


def _valid_photo_urls(value: Any) -> list[str]:
    """Keep complete official 12123 photo stream URLs, deduplicated by index."""
    if not isinstance(value, list):
        return []

    result: list[str] = []
    seen: set[tuple[str, str]] = set()
    for raw_url in value:
        if not isinstance(raw_url, str):
            continue
        url = raw_url.strip()
        try:
            parsed = urlsplit(url)
        except ValueError:
            continue
        if parsed.scheme not in {"http", "https"}:
            continue
        if not parsed.path.endswith("/app/gw/netvio/photo/gw/stream"):
            continue
        query = parse_qs(parsed.query)
        xh = (query.get("xh") or [""])[0]
        idx = (query.get("idx") or [""])[0]
        token = (query.get("token") or [""])[0]
        if not xh or not idx.isdigit() or not token:
            continue
        key = (xh, idx)
        if key in seen:
            continue
        seen.add(key)
        result.append(url)
    return result


def _valid_local_photo_urls(value: Any) -> list[str]:
    """Keep local paths and valid official fallbacks from the cached photo list."""
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for raw_url in value:
        if not isinstance(raw_url, str):
            continue
        url = raw_url.strip()
        if url.startswith("/12123-images/") or url in _valid_photo_urls([url]):
            result.append(url)
    return result
