"""Configure and verify 12123 authorization and login."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import instance_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from ..client.api import (
    JiaoguanApiClient,
    JiaoguanApiError,
    JiaoguanAuthorizationError,
    JiaoguanConnectionError,
    JiaoguanLoginRequiredError,
)
from ..const import (
    CONF_ACCESS_TOKEN,
    CONF_AUTHORIZATION_CODE,
    CONF_AUTHORIZATION_LABEL,
    CONF_BACKEND_URL,
    CONF_DEVICE_ID,
    CONF_HA_INSTANCE_ID,
    CONF_LOGIN_DATA,
    CONF_MOBILE_SESSION_ID,
    CONF_SFZMHM,
    CONF_SFZMHM_FULL,
    CONF_SSO_TOKEN,
    DEFAULT_BACKEND_URL,
    DOMAIN,
)
from .options import OptionsFlowHandler


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle 12123 config flow: authorization code verification then login."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Open the refresh interval options for an existing entry."""
        return OptionsFlowHandler()

    def __init__(self) -> None:
        self._authorization_code: str | None = None
        self._backend_url: str = DEFAULT_BACKEND_URL
        self._access_token: str | None = None
        self._authorization_label: str = "12123"
        self._sfzmhm: str | None = None
        self._ha_instance_id: str | None = None
        self._target_entry_id: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: Input authorization code and backend url."""
        errors: dict[str, str] = {}
        if user_input is not None:
            auth_code = str(user_input.get(CONF_AUTHORIZATION_CODE) or "").strip()
            backend_url = DEFAULT_BACKEND_URL
            ha_instance_id = await instance_id.async_get(self.hass)

            client = JiaoguanApiClient(async_get_clientsession(self.hass), backend_url)
            try:
                result = await client.async_authorize(auth_code, ha_instance_id)
                raw_data = result.get("data") if isinstance(result, dict) else None
                data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
                access_token = str(data.get("access_token") or "").strip()
                if not access_token:
                    raise JiaoguanAuthorizationError("未签发有效访问令牌")

                self._authorization_code = auth_code
                self._backend_url = backend_url
                self._access_token = access_token
                self._ha_instance_id = ha_instance_id
                self._authorization_label = str(data.get("authorization_label") or "12123")

                # 无论授权码是否已经绑定过账号，都进入登录步骤获取本次账号的完整身份证号。
                # 同一个 Authorization 因而可以继续添加第二个或更多 12123 账号。
                return await self.async_step_login()
            except JiaoguanAuthorizationError:
                errors["base"] = "invalid_authorization"
            except JiaoguanConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_AUTHORIZATION_CODE): str,
            }),
            errors=errors,
        )

    async def async_step_login(self, user_input: dict[str, Any] | None = None):
        """Step 2: Submit official 12123 capture credentials under the acquired token."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = JiaoguanApiClient(
                async_get_clientsession(self.hass),
                self._backend_url,
                self._access_token,
                self._sfzmhm,
            )
            try:
                result = await client.async_login(
                    device_id=user_input[CONF_DEVICE_ID].strip(),
                    data=user_input[CONF_LOGIN_DATA].strip(),
                    mobile_session_id=user_input[CONF_MOBILE_SESSION_ID].strip(),
                    token=user_input[CONF_SSO_TOKEN].strip(),
                )
                if result.get("data", {}).get("db_saved") is False:
                    errors["base"] = "login_failed"
                else:
                    sfzmhm = client.sfzmhm
                    if not _valid_sfzmhm(sfzmhm):
                        errors["base"] = "sfzmhm_unavailable"
                    else:
                        self._sfzmhm = sfzmhm

                        # 账号维度去重：Authorization 相同但 sfzmhm 不同允许并存；
                        # 同一 Authorization + 同一身份证只允许一个 HA 条目。
                        account_unique_id = hashlib.sha256(
                            f"{self._authorization_code}|{sfzmhm}".encode()
                        ).hexdigest()
                        if not self._target_entry_id:
                            await self.async_set_unique_id(account_unique_id)
                            self._abort_if_unique_id_configured()
                            for existing in self.hass.config_entries.async_entries(DOMAIN):
                                if (
                                    existing.data.get(CONF_AUTHORIZATION_CODE) == self._authorization_code
                                    and str(existing.data.get(CONF_SFZMHM_FULL) or existing.data.get(CONF_SFZMHM) or "").strip().upper() == sfzmhm
                                ):
                                    return self.async_abort(reason="already_configured")

                        await client.async_fetch_overview()
                        entry_data = {
                            CONF_AUTHORIZATION_CODE: self._authorization_code,
                            CONF_BACKEND_URL: self._backend_url,
                            CONF_ACCESS_TOKEN: self._access_token,
                            CONF_SFZMHM: sfzmhm,
                            CONF_SFZMHM_FULL: sfzmhm,
                            CONF_AUTHORIZATION_LABEL: self._authorization_label,
                            CONF_HA_INSTANCE_ID: self._ha_instance_id,
                        }
                        if self._target_entry_id:
                            entry = self.hass.config_entries.async_get_entry(self._target_entry_id)
                            return self.async_update_reload_and_abort(
                                entry,
                                data_updates=entry_data,
                            )
                        return self.async_create_entry(
                            title=self._authorization_label,
                            data=entry_data,
                        )
            except JiaoguanAuthorizationError:
                errors["base"] = "login_failed"
            except JiaoguanLoginRequiredError:
                errors["base"] = "login_failed"
            except JiaoguanConnectionError:
                errors["base"] = "cannot_connect"
            except JiaoguanApiError:
                errors["base"] = "login_failed"

        return self._login_form(errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Re-authenticate an existing entry using its saved authorization code."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if not entry:
            return self.async_abort(reason="reauth_failed")

        self._target_entry_id = entry.entry_id
        self._authorization_code = entry.data.get(CONF_AUTHORIZATION_CODE)
        self._backend_url = entry.data.get(CONF_BACKEND_URL, DEFAULT_BACKEND_URL)
        self._access_token = entry.data.get(CONF_ACCESS_TOKEN)
        self._authorization_label = entry.data.get(CONF_AUTHORIZATION_LABEL) or "12123"
        self._sfzmhm = entry.data.get(CONF_SFZMHM_FULL) or entry.data.get(CONF_SFZMHM)
        self._ha_instance_id = entry.data.get(CONF_HA_INSTANCE_ID) or str(self.hass.data.get("core.uuid") or "")

        if self._authorization_code:
            # 尝试刷新 access_token
            client = JiaoguanApiClient(async_get_clientsession(self.hass), self._backend_url)
            try:
                res = await client.async_authorize(self._authorization_code, self._ha_instance_id)
                raw_data = res.get("data") if isinstance(res, dict) else None
                data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
                if data.get("access_token"):
                    self._access_token = str(data["access_token"]).strip()
                if data.get("authorization_label"):
                    self._authorization_label = str(data["authorization_label"]).strip()
            except Exception:
                pass
            return await self.async_step_login()

        return await self.async_step_user()

    def _login_form(self, errors: dict[str, str] | None = None):
        return self.async_show_form(
            step_id="login",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_LOGIN_DATA): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                vol.Required(CONF_MOBILE_SESSION_ID): str,
                vol.Required(CONF_SSO_TOKEN): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            }),
            errors=errors or {},
        )


def _valid_sfzmhm(value: Any) -> bool:
    """Validate the complete 18-character identity required by the relay."""
    return bool(re.fullmatch(
        r"[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])"
        r"(0[1-9]|[12]\d|3[01])\d{3}[\dX]",
        str(value or "").strip().upper(),
        re.IGNORECASE,
    ))
