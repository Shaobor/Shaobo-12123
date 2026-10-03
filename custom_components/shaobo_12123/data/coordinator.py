"""Coordinator for 12123 dashboard data."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit

import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ..client.api import JiaoguanApiClient, JiaoguanApiError, JiaoguanAuthorizationError, JiaoguanLoginRequiredError
from ..const import (
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_VIOLATION_SCAN_INTERVAL_MINUTES,
    CONF_MESSAGE_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MIN_SCAN_INTERVAL_MINUTES,
    MIN_VIOLATION_SCAN_INTERVAL_MINUTES,
    MIN_MESSAGE_SCAN_INTERVAL_MINUTES,
)


class JiaoguanDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch dashboard data while throttling the more expensive violation request."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: JiaoguanApiClient) -> None:
        try:
            scan_interval_minutes = int(
                entry.options.get(CONF_SCAN_INTERVAL_MINUTES, DEFAULT_SCAN_INTERVAL_MINUTES)
            )
        except (TypeError, ValueError):
            scan_interval_minutes = DEFAULT_SCAN_INTERVAL_MINUTES
        scan_interval_minutes = max(scan_interval_minutes, MIN_SCAN_INTERVAL_MINUTES)
        try:
            violation_scan_interval_minutes = int(
                entry.options.get(
                    CONF_VIOLATION_SCAN_INTERVAL_MINUTES,
                    DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES,
                )
            )
        except (TypeError, ValueError):
            violation_scan_interval_minutes = DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES
        violation_scan_interval_minutes = max(
            violation_scan_interval_minutes,
            MIN_VIOLATION_SCAN_INTERVAL_MINUTES,
        )
        try:
            message_scan_interval_minutes = int(
                entry.options.get(CONF_MESSAGE_SCAN_INTERVAL_MINUTES, scan_interval_minutes)
            )
        except (TypeError, ValueError):
            message_scan_interval_minutes = scan_interval_minutes
        message_scan_interval_minutes = max(
            message_scan_interval_minutes,
            MIN_MESSAGE_SCAN_INTERVAL_MINUTES,
        )
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=min(
                    scan_interval_minutes,
                    violation_scan_interval_minutes,
                    message_scan_interval_minutes,
                )
            ),
        )
        self.client = client
        self._overview_interval = timedelta(minutes=scan_interval_minutes)
        self._violation_scan_interval = timedelta(minutes=violation_scan_interval_minutes)
        self._message_scan_interval = timedelta(minutes=message_scan_interval_minutes)
        self._overview_cache: dict[str, Any] | None = None
        self._last_overview_fetch = 0.0
        self._violation_cache: dict[str, Any] | None = None
        self._last_violation_fetch = 0.0
        self._business_cache: dict[str, Any] | None = None
        self._service_cache: dict[str, Any] | None = None
        self._last_message_fetch = 0.0
        self._force_violation_refresh = False
        self._violation_image_dir = Path(hass.config.path("12123", "violations"))
        self._violation_image_dir.mkdir(parents=True, exist_ok=True)
        self._last_data_update: datetime | None = None

    @property
    def scan_interval_minutes(self) -> int:
        """Return the configured interval used for normal dashboard data."""
        return int(self._overview_interval.total_seconds() // 60)

    @property
    def violation_scan_interval_minutes(self) -> int:
        """Return the configured interval used for violation data and photos."""
        return int(self._violation_scan_interval.total_seconds() // 60)

    @property
    def message_scan_interval_minutes(self) -> int:
        """Return the configured message-center refresh interval."""
        return int(self._message_scan_interval.total_seconds() // 60)

    def _reset_poll_interval(self) -> None:
        """Avoid rapid retries when a dynamically scheduled request fails."""
        self.update_interval = min(
            self._overview_interval,
            self._violation_scan_interval,
            self._message_scan_interval,
        )

    @property
    def last_data_update(self) -> datetime | None:
        """Return when the last successful data request finished."""
        return self._last_data_update

    @callback
    def async_force_violation_refresh(self) -> None:
        """Make the next coordinator refresh fetch violations and images immediately."""
        self._force_violation_refresh = True

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            now = monotonic()
            fetched = False
            if (
                self._overview_cache is None
                or now - self._last_overview_fetch >= self._overview_interval.total_seconds()
            ):
                overview = await self.client.async_fetch_overview()
                self._overview_cache = overview.get("data", {})
                self._last_overview_fetch = monotonic()
                fetched = True
            should_fetch_violations = (
                self._violation_cache is None
                or self._force_violation_refresh
                or now - self._last_violation_fetch >= self._violation_scan_interval.total_seconds()
            )
            if should_fetch_violations:
                violations = await self.client.async_fetch_violations()
                await self._async_download_violation_images(violations)
                self._violation_cache = violations
                self._last_violation_fetch = monotonic()
                self._force_violation_refresh = False
                fetched = True
            if (
                self._business_cache is None
                or self._service_cache is None
                or now - self._last_message_fetch >= self._message_scan_interval.total_seconds()
            ):
                business_notices = await self.client.async_fetch_messages("2")
                service_reminders = await self.client.async_fetch_messages("1")
                self._business_cache = business_notices
                self._service_cache = service_reminders
                self._last_message_fetch = monotonic()
                fetched = True
            if fetched:
                self._last_data_update = datetime.now(timezone.utc)
            next_due = min(
                self._last_overview_fetch + self._overview_interval.total_seconds(),
                self._last_violation_fetch + self._violation_scan_interval.total_seconds(),
                self._last_message_fetch + self._message_scan_interval.total_seconds(),
            )
            self.update_interval = timedelta(seconds=max(1, next_due - monotonic()))
            return {
                "overview": self._overview_cache or {},
                "violations": self._violation_cache or {"data": []},
                "business_notices": self._business_cache or {"data": []},
                "service_reminders": self._service_cache or {"data": []},
            }
        except (JiaoguanAuthorizationError, JiaoguanLoginRequiredError) as err:
            self._reset_poll_interval()
            raise ConfigEntryAuthFailed(str(err)) from err
        except JiaoguanApiError as err:
            self._reset_poll_interval()
            raise UpdateFailed(str(err)) from err
        except Exception:
            self._reset_poll_interval()
            raise

    async def _async_download_violation_images(self, payload: dict[str, Any]) -> None:
        """Cache official violation photos locally and expose HA-served paths."""
        vehicles = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(vehicles, list):
            return

        semaphore = asyncio.Semaphore(4)
        jobs = []
        for vehicle in vehicles:
            if not isinstance(vehicle, dict):
                continue
            for violation in vehicle.get("violations") or []:
                if isinstance(violation, dict):
                    jobs.append(self._async_cache_violation_photos(violation, semaphore))
        if jobs:
            await asyncio.gather(*jobs)

    async def _async_cache_violation_photos(self, violation: dict[str, Any], semaphore: Any) -> None:
        photos = violation.get("photos")
        if not isinstance(photos, list):
            return
        local_photos: list[str] = []
        for index, raw_url in enumerate(photos, start=1):
            url = str(raw_url or "").strip()
            if not _is_official_photo_url(url):
                continue
            filename = _photo_filename(violation, url, index)
            target = self._violation_image_dir / filename
            if not target.is_file() or target.stat().st_size == 0:
                try:
                    async with semaphore:
                        async with self.client.session.get(
                            url,
                            headers={
                                "User-Agent": "12123/3.5.7 (iPhone; iOS 18.0; Scale/3.00)",
                                "Accept": "image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5",
                                "Accept-Language": "zh-CN,zh-Hans;q=0.9",
                            },
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as response:
                            if response.status != 200:
                                local_photos.append(url)
                                continue
                            content = await response.read()
                        if content:
                            await self.hass.async_add_executor_job(target.write_bytes, content)
                except (aiohttp.ClientError, TimeoutError, OSError):
                    local_photos.append(url)
                    continue
            if target.is_file() and target.stat().st_size > 0:
                local_photos.append(f"/12123-images/{filename}")
            else:
                local_photos.append(url)
        violation["local_photos"] = local_photos


def _is_official_photo_url(url: str) -> bool:
    """Only download photo URLs served by the official 122.gov.cn domain."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (host == "122.gov.cn" or host.endswith(".122.gov.cn"))


def _photo_filename(violation: dict[str, Any], url: str, index: int) -> str:
    """Return a stable, filesystem-safe name for one violation photo."""
    xh = "".join(ch for ch in str(violation.get("xh") or "") if ch.isalnum())
    if not xh:
        xh = sha256(url.encode("utf-8")).hexdigest()[:24]
    return f"{xh}_{index}.jpg"
