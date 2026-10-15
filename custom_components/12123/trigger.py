"""Provide target-based automation triggers for the 12123 integration."""

from __future__ import annotations

from typing import ClassVar

import voluptuous as vol

from homeassistant.const import ATTR_DEVICE_ID, CONF_TARGET
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.trigger import (
    Trigger,
    TriggerActionRunner,
    TriggerConfig,
)
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_TARGET_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TARGET): vol.Schema(
            {
                vol.Required(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
            }
        ),
    }
)


class _12123EventTrigger(Trigger):
    """Base class for a target-based 12123 event trigger."""

    event_type: ClassVar[str]
    display_name: ClassVar[str]

    @classmethod
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate the selected target device(s)."""
        del hass
        return _TARGET_SCHEMA(config)

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        """Initialize the trigger."""
        super().__init__(hass, config)
        self._target = config.target or {}

    async def async_attach_runner(
        self,
        run_action: TriggerActionRunner,
        did_not_trigger: object | None = None,
    ) -> CALLBACK_TYPE:
        """Listen for the 12123 event for the selected device(s)."""
        del did_not_trigger
        device_ids = set(self._target.get(ATTR_DEVICE_ID, []))

        @callback
        def handle_event(event: Event) -> None:
            """Forward matching 12123 events to the automation action."""
            event_device_id = event.data.get(ATTR_DEVICE_ID)
            if event_device_id not in device_ids:
                return

            run_action(
                {
                    ATTR_DEVICE_ID: event_device_id,
                    "event_type": event.event_type,
                    "event_data": dict(event.data),
                },
                f"{self.display_name}（设备 {event_device_id}）",
                event.context,
            )

        return self._hass.bus.async_listen(self.event_type, handle_event)


class WeitingAlertTrigger(_12123EventTrigger):
    """Trigger when a parking-removal reminder is received."""

    event_type = f"{DOMAIN}_weiting_alert"
    display_name = "收到违停驶离提醒"


class NewViolationTrigger(_12123EventTrigger):
    """Trigger when a new vehicle violation is found."""

    event_type = f"{DOMAIN}_new_violation"
    display_name = "产生新的车辆违章"


class NewBusinessNoticeTrigger(_12123EventTrigger):
    """Trigger when a new business notice is received."""

    event_type = f"{DOMAIN}_new_business_notice"
    display_name = "收到新的业务告知"


class NewServiceMessageTrigger(_12123EventTrigger):
    """Trigger when a new service reminder is received."""

    event_type = f"{DOMAIN}_new_service_message"
    display_name = "收到新的服务提醒消息"


async def async_get_triggers(
    hass: HomeAssistant,
) -> dict[str, type[Trigger]]:
    """Return target-based 12123 triggers."""
    del hass
    return {
        "weiting_alert": WeitingAlertTrigger,
        "new_violation": NewViolationTrigger,
        "new_business_notice": NewBusinessNoticeTrigger,
        "new_service_message": NewServiceMessageTrigger,
    }
