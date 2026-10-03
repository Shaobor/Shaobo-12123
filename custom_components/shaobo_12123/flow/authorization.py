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


def _mask_name(name: str) -> str:
    """车主姓名脱敏：2字脱敏为'张*'，3字脱敏为'王*博'，4字及以上脱敏为'诸**明'。"""
    name = (name or "").strip()
    if not name:
        return ""
    if len(name) == 1:
        return name
    if len(name) == 2:
        return f"{name[0]}*"
    return f"{name[0]}{'*' * (len(name) - 2)}{name[-1]}"


def _mask_display_name(disp: str = "", name: str = "", sf: str = "") -> str:
    """格式化展示名称：带脱敏姓名与脱敏身份证号。"""
    masked_sf = f"{sf[:6]}********{sf[-4:]}" if len(sf) >= 15 else sf
    if name:
        m_name = _mask_name(name)
        return f"{m_name} ({masked_sf})" if masked_sf else m_name

    disp = (disp or "").strip()
    match = re.match(r"^([^\(\（]+)[\(\（](.*)[\)\）]$", disp)
    if match:
        orig_name = match.group(1).strip()
        sf_part = match.group(2).strip()
        return f"{_mask_name(orig_name)} ({sf_part})"
    if disp and not sf:
        return _mask_name(disp)
    return disp


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
        self._server_accounts: list[dict[str, Any]] = []

    def _parse_server_accounts(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """从服务端返回提纯已在服务器上登录的 12123 车主账号列表。"""
        accounts = []
        raw_list = data.get("accounts")
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, dict):
                    sf = str(item.get("sfzmhm") or "").strip().upper()
                    if sf:
                        masked = str(item.get("sfzmhm_masked") or sf).strip().upper()
                        xm = str(item.get("xm") or item.get("user_name") or "").strip()
                        raw_disp = str(item.get("display_name") or "").strip()
                        disp = _mask_display_name(raw_disp, xm, sf) or masked
                        accounts.append({
                            "sfzmhm": sf,
                            "sfzmhm_masked": masked,
                            "display_name": disp,
                            "user_name": xm,
                        })
        if not accounts and data.get("is_bound"):
            bound_sf = str(data.get("bound_sfzmhm") or data.get("sfzmhm") or "").strip().upper()
            if bound_sf:
                masked = f"{bound_sf[:6]}********{bound_sf[-4:]}" if len(bound_sf) >= 15 else bound_sf
                accounts.append({
                    "sfzmhm": bound_sf,
                    "sfzmhm_masked": masked,
                    "display_name": masked,
                })
        return accounts

    async def _async_discover_server_accounts(
        self,
        client: JiaoguanApiClient | None,
        auth_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """多源动态探查服务器上已有车主档案与本地缓存车主列表。"""
        accounts_map: dict[str, dict[str, Any]] = {}

        # 1. 尝试从 authorize 接口返回数据提取
        for acc in self._parse_server_accounts(auth_data):
            sf = acc.get("sfzmhm")
            if sf:
                accounts_map[sf] = acc

        # 2. 尝试从服务端 /api/admin/repair_users_table 提取已在服务器登录的车主
        if client:
            try:
                repair_res = await client._post("/api/admin/repair_users_table", {})
                current_users = (
                    repair_res.get("current_users")
                    or (repair_res.get("data", {}) if isinstance(repair_res.get("data"), dict) else {}).get("current_users")
                    or []
                )
                if isinstance(current_users, list):
                    for u in current_users:
                        if isinstance(u, dict):
                            sf = str(u.get("sfzmhm") or "").strip().upper()
                            xm = str(u.get("xm") or "").strip()
                            if sf:
                                masked = f"{sf[:6]}********{sf[-4:]}" if len(sf) >= 15 else sf
                                disp = _mask_display_name("", xm, sf)
                                accounts_map[sf] = {
                                    "sfzmhm": sf,
                                    "sfzmhm_masked": masked,
                                    "display_name": disp,
                                    "user_name": xm,
                                }
            except Exception:
                pass

        # 3. 尝试从 HA 本地专属存储 (.storage/Shaobo_12123) 提取
        try:
            from ..storage import async_load_12123_accounts
            saved = await async_load_12123_accounts(self.hass)
            for sf, acc in saved.items():
                if sf and sf != "draft_authorization_code" and isinstance(acc, dict):
                    sf_clean = str(sf).strip().upper()
                    if sf_clean not in accounts_map:
                        xm = str(acc.get("user_name") or acc.get("xm") or "").strip()
                        masked = f"{sf_clean[:6]}********{sf_clean[-4:]}" if len(sf_clean) >= 15 else sf_clean
                        raw_disp = str(acc.get("display_name") or "").strip()
                        disp = _mask_display_name(raw_disp, xm, sf_clean)
                        accounts_map[sf_clean] = {
                            "sfzmhm": sf_clean,
                            "sfzmhm_masked": masked,
                            "display_name": disp,
                            "user_name": xm,
                        }
        except Exception:
            pass

        return list(accounts_map.values())

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step 1: Input authorization code and backend url."""
        errors: dict[str, str] = {}

        # 自动提取现有条目或专属存储中的授权码作为默认预填值
        existing_code = ""
        existing_access_token = ""
        existing_label = "12123"
        existing_backend_url = DEFAULT_BACKEND_URL

        for existing in self.hass.config_entries.async_entries(DOMAIN):
            code = existing.data.get(CONF_AUTHORIZATION_CODE)
            if code:
                existing_code = str(code).strip()
                existing_access_token = str(existing.data.get(CONF_ACCESS_TOKEN) or "").strip()
                existing_label = str(existing.data.get(CONF_AUTHORIZATION_LABEL) or "12123").strip()
                existing_backend_url = str(existing.data.get(CONF_BACKEND_URL) or DEFAULT_BACKEND_URL).strip()
                break

        if not existing_code:
            try:
                from ..storage import async_load_12123_accounts, AuthorizationDraftStore
                draft = await AuthorizationDraftStore(self.hass).async_load()
                if draft and draft.get("authorization_code"):
                    existing_code = str(draft["authorization_code"]).strip()
                else:
                    accounts = await async_load_12123_accounts(self.hass)
                    for acc in accounts.values():
                        if isinstance(acc, dict) and acc.get(CONF_AUTHORIZATION_CODE):
                            existing_code = str(acc[CONF_AUTHORIZATION_CODE]).strip()
                            existing_access_token = str(acc.get(CONF_ACCESS_TOKEN) or "").strip()
                            break
            except Exception:
                pass

        # 如果已有授权码且首次进入，自动静默鉴权；检查服务器已有账号
        if user_input is None and existing_code:
            ha_instance_id = await instance_id.async_get(self.hass)
            backend_url = existing_backend_url or DEFAULT_BACKEND_URL
            access_token = existing_access_token or existing_code
            authorization_label = existing_label or "12123"
            data: dict[str, Any] = {}
            client = None

            try:
                client = JiaoguanApiClient(async_get_clientsession(self.hass), backend_url, access_token)
                result = await client.async_authorize(existing_code, ha_instance_id)
                raw_data = result.get("data") if isinstance(result, dict) else None
                if isinstance(raw_data, dict):
                    data = raw_data
                    access_token = str(data.get("access_token") or access_token).strip()
                    authorization_label = str(data.get("authorization_label") or authorization_label).strip()
                    client.set_access_token(access_token)
            except JiaoguanAuthorizationError:
                # 仅当服务端明确返回 401 未授权/被禁用时，才打回并拦截报错
                errors["base"] = "invalid_authorization"
                schema_dict = {vol.Required(CONF_AUTHORIZATION_CODE, default=existing_code): str}
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(schema_dict),
                    errors=errors,
                )
            except Exception:
                # 遇到 503 等非 401 异常时，容灾复用已有凭据继续完成流程，绝不打回弹窗！
                pass

            self._authorization_code = existing_code
            self._backend_url = backend_url
            self._access_token = access_token
            self._ha_instance_id = ha_instance_id
            self._authorization_label = authorization_label
            self._server_accounts = await self._async_discover_server_accounts(client, data)

            if self._server_accounts:
                return await self.async_step_select_account()
            return await self.async_step_login()

        if user_input is not None:
            auth_code = str(user_input.get(CONF_AUTHORIZATION_CODE) or "").strip()
            backend_url = DEFAULT_BACKEND_URL
            ha_instance_id = await instance_id.async_get(self.hass)
            access_token = auth_code
            authorization_label = "12123"
            data: dict[str, Any] = {}
            client = None

            try:
                client = JiaoguanApiClient(async_get_clientsession(self.hass), backend_url, access_token)
                result = await client.async_authorize(auth_code, ha_instance_id)
                raw_data = result.get("data") if isinstance(result, dict) else None
                if isinstance(raw_data, dict):
                    data = raw_data
                    access_token = str(data.get("access_token") or access_token).strip()
                    authorization_label = str(data.get("authorization_label") or authorization_label).strip()
                    client.set_access_token(access_token)
            except JiaoguanAuthorizationError:
                errors["base"] = "invalid_authorization"
                schema_dict = {vol.Required(CONF_AUTHORIZATION_CODE, default=auth_code): str}
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(schema_dict),
                    errors=errors,
                )
            except Exception:
                pass

            self._authorization_code = auth_code
            self._backend_url = backend_url
            self._access_token = access_token
            self._ha_instance_id = ha_instance_id
            self._authorization_label = authorization_label
            self._server_accounts = await self._async_discover_server_accounts(client, data)

            # 保存草稿以备后续使用
            try:
                from ..storage import AuthorizationDraftStore
                await AuthorizationDraftStore(self.hass).async_save(auth_code)
            except Exception:
                pass

            if self._server_accounts:
                return await self.async_step_select_account()
            return await self.async_step_login()

        schema_dict: dict[Any, Any] = {}
        if existing_code:
            schema_dict[vol.Required(CONF_AUTHORIZATION_CODE, default=existing_code)] = str
        else:
            schema_dict[vol.Required(CONF_AUTHORIZATION_CODE)] = str

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )

    async def async_step_select_account(self, user_input: dict[str, Any] | None = None):
        """Step 1.5: Select an existing logged-in account on server or bind a new one."""
        errors: dict[str, str] = {}

        # 收集当前 HA 实例所有已配置账号的特征（包含完整 sfzmhm 及脱敏掩码）
        configured_ids = set()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            sf_full = str(entry.data.get(CONF_SFZMHM_FULL) or entry.data.get(CONF_SFZMHM) or "").strip().upper()
            if sf_full:
                configured_ids.add(sf_full)
                if len(sf_full) >= 15:
                    configured_ids.add(f"{sf_full[:6]}********{sf_full[-4:]}")

        account_options = {}
        for acc in self._server_accounts:
            sf = acc["sfzmhm"]
            masked = acc["sfzmhm_masked"]
            display = acc["display_name"]
            is_added = (sf in configured_ids) or (masked in configured_ids)
            label = f"{display} (已添加)" if is_added else display
            account_options[sf] = label

        account_options["__new_account__"] = "➕ 绑定新车主账号（录入抓包参数）"

        if user_input is not None:
            choice = str(user_input.get("selected_account") or "").strip()
            if choice == "__new_account__":
                return await self.async_step_login()

            # 校验是否已经添加过
            acc = next((a for a in self._server_accounts if a["sfzmhm"] == choice), None)
            choice_masked = acc["sfzmhm_masked"] if acc else choice
            if (choice in configured_ids) or (choice_masked in configured_ids):
                errors["base"] = "account_already_configured"
            else:
                sfzmhm_to_use = choice
                self._sfzmhm = sfzmhm_to_use

                # 账号维度去重
                account_unique_id = hashlib.sha256(
                    f"{self._authorization_code}|{sfzmhm_to_use}".encode()
                ).hexdigest()
                await self.async_set_unique_id(account_unique_id)
                self._abort_if_unique_id_configured()

                client = JiaoguanApiClient(
                    async_get_clientsession(self.hass),
                    self._backend_url,
                    self._access_token,
                    sfzmhm_to_use,
                )
                try:
                    await client.async_fetch_overview()
                except JiaoguanLoginRequiredError:
                    # 若服务端对应车主的 12123 会话已过期失效，自动流转到抓包页面让用户输入新参数续期
                    return await self.async_step_login()
                except Exception:
                    pass

                entry_data = {
                    CONF_AUTHORIZATION_CODE: self._authorization_code,
                    CONF_BACKEND_URL: self._backend_url,
                    CONF_ACCESS_TOKEN: self._access_token,
                    CONF_SFZMHM: sfzmhm_to_use,
                    CONF_SFZMHM_FULL: sfzmhm_to_use,
                    CONF_AUTHORIZATION_LABEL: self._authorization_label,
                    CONF_HA_INSTANCE_ID: self._ha_instance_id,
                }
                title = acc.get("display_name") if acc else sfzmhm_to_use
                try:
                    from ..storage import async_save_12123_account
                    await async_save_12123_account(
                        self.hass,
                        sfzmhm_to_use,
                        {
                            CONF_AUTHORIZATION_CODE: self._authorization_code,
                            CONF_BACKEND_URL: self._backend_url,
                            CONF_ACCESS_TOKEN: self._access_token,
                            CONF_SFZMHM: sfzmhm_to_use,
                            CONF_SFZMHM_FULL: sfzmhm_to_use,
                            CONF_AUTHORIZATION_LABEL: self._authorization_label,
                            "display_name": title,
                            "user_name": acc.get("user_name") if acc else "",
                        },
                    )
                except Exception:
                    pass

                return self.async_create_entry(
                    title=title,
                    data=entry_data,
                )

        default_choice = "__new_account__"
        for sf, label in account_options.items():
            if sf != "__new_account__" and "(已添加)" not in label:
                default_choice = sf
                break

        return self.async_show_form(
            step_id="select_account",
            data_schema=vol.Schema({
                vol.Required("selected_account", default=default_choice): vol.In(account_options),
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

                        xm = ""
                        try:
                            overview_res = await client.async_fetch_overview()
                            user_info = overview_res.get("data", {}).get("user_info", {})
                            xm = str(user_info.get("xm") or "").strip()
                        except Exception:
                            pass

                        title = _mask_display_name("", xm, sfzmhm) or self._authorization_label

                        entry_data = {
                            CONF_AUTHORIZATION_CODE: self._authorization_code,
                            CONF_BACKEND_URL: self._backend_url,
                            CONF_ACCESS_TOKEN: self._access_token,
                            CONF_SFZMHM: sfzmhm,
                            CONF_SFZMHM_FULL: sfzmhm,
                            CONF_AUTHORIZATION_LABEL: self._authorization_label,
                            CONF_HA_INSTANCE_ID: self._ha_instance_id,
                        }

                        try:
                            from ..storage import async_save_12123_account
                            await async_save_12123_account(
                                self.hass,
                                sfzmhm,
                                {
                                    CONF_AUTHORIZATION_CODE: self._authorization_code,
                                    CONF_BACKEND_URL: self._backend_url,
                                    CONF_ACCESS_TOKEN: self._access_token,
                                    CONF_SFZMHM: sfzmhm,
                                    CONF_SFZMHM_FULL: sfzmhm,
                                    CONF_AUTHORIZATION_LABEL: self._authorization_label,
                                    "display_name": title,
                                    "user_name": xm,
                                },
                            )
                        except Exception:
                            pass

                        if self._target_entry_id:
                            entry = self.hass.config_entries.async_get_entry(self._target_entry_id)
                            return self.async_update_reload_and_abort(
                                entry,
                                data_updates=entry_data,
                            )
                        return self.async_create_entry(
                            title=title,
                            data=entry_data,
                        )
            except JiaoguanAuthorizationError:
                errors["base"] = "invalid_authorization"
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
