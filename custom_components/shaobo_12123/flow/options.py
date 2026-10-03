"""Options flow for the 12123 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import NumberSelector, NumberSelectorConfig, NumberSelectorMode

from ..const import (
    CONF_SCAN_INTERVAL_MINUTES,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    CONF_VIOLATION_SCAN_INTERVAL_MINUTES,
    DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES,
    MIN_VIOLATION_SCAN_INTERVAL_MINUTES,
    CONF_MESSAGE_SCAN_INTERVAL_MINUTES,
    MIN_MESSAGE_SCAN_INTERVAL_MINUTES,
)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Configure the polling interval without redoing authorization."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Handle the refresh interval form."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                interval = int(user_input[CONF_SCAN_INTERVAL_MINUTES])
                violation_interval = int(user_input[CONF_VIOLATION_SCAN_INTERVAL_MINUTES])
                message_interval = int(user_input[CONF_MESSAGE_SCAN_INTERVAL_MINUTES])
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_scan_interval"
            else:
                if interval < MIN_SCAN_INTERVAL_MINUTES:
                    errors["base"] = "scan_interval_too_short"
                elif violation_interval < MIN_VIOLATION_SCAN_INTERVAL_MINUTES:
                    errors["base"] = "violation_scan_interval_too_short"
                elif message_interval < MIN_MESSAGE_SCAN_INTERVAL_MINUTES:
                    errors["base"] = "message_scan_interval_too_short"
                else:
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_SCAN_INTERVAL_MINUTES: interval,
                            CONF_VIOLATION_SCAN_INTERVAL_MINUTES: violation_interval,
                            CONF_MESSAGE_SCAN_INTERVAL_MINUTES: message_interval,
                        },
                    )

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL_MINUTES,
            DEFAULT_SCAN_INTERVAL_MINUTES,
        )
        try:
            current = max(int(current), MIN_SCAN_INTERVAL_MINUTES)
        except (TypeError, ValueError):
            current = DEFAULT_SCAN_INTERVAL_MINUTES
        violation_current = self.config_entry.options.get(
            CONF_VIOLATION_SCAN_INTERVAL_MINUTES,
            DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES,
        )
        try:
            violation_current = max(int(violation_current), MIN_VIOLATION_SCAN_INTERVAL_MINUTES)
        except (TypeError, ValueError):
            violation_current = DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES
        message_current = self.config_entry.options.get(
            CONF_MESSAGE_SCAN_INTERVAL_MINUTES,
            current,
        )
        try:
            message_current = max(int(message_current), MIN_MESSAGE_SCAN_INTERVAL_MINUTES)
        except (TypeError, ValueError):
            message_current = current
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_SCAN_INTERVAL_MINUTES,
                    default=current,
                ): NumberSelector(
                    NumberSelectorConfig(
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="分钟",
                    )
                ),
                vol.Required(
                    CONF_VIOLATION_SCAN_INTERVAL_MINUTES,
                    default=violation_current,
                ): NumberSelector(
                    NumberSelectorConfig(
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="分钟",
                    )
                ),
                vol.Required(
                    CONF_MESSAGE_SCAN_INTERVAL_MINUTES,
                    default=message_current,
                ): NumberSelector(
                    NumberSelectorConfig(
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="分钟",
                    )
                ),
            }),
            errors=errors,
        )
