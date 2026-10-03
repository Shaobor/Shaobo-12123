"""HTTP client for the 12123 relay service."""

from __future__ import annotations

import re
from typing import Any

import aiohttp

class JiaoguanApiError(Exception):
    """Base error returned by the relay service."""


class JiaoguanAuthorizationError(JiaoguanApiError):
    """The authorization code or HA access token is invalid."""


class JiaoguanLoginRequiredError(JiaoguanApiError):
    """The official 12123 login session needs to be refreshed."""


class JiaoguanConnectionError(JiaoguanApiError):
    """The relay service cannot be reached."""


class JiaoguanApiClient:
    """Calls only the user's relay service, never the official 12123 endpoints."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        access_token: str | None = None,
        sfzmhm: str | None = None,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._access_token = access_token.strip() if access_token else None
        self._sfzmhm = sfzmhm.strip().upper() if sfzmhm else None

    @property
    def access_token(self) -> str | None:
        """Return the current HA access token."""
        return self._access_token

    def set_access_token(self, value: str | None) -> None:
        """Set or update the HA access token."""
        self._access_token = value.strip() if value else None

    @property
    def session(self) -> aiohttp.ClientSession:
        """Expose the configured HA session for downloading official photos."""
        return self._session

    @property
    def sfzmhm(self) -> str | None:
        """Return the complete owner identity learned during login, if available."""
        return self._sfzmhm

    def set_sfzmhm(self, value: str | None) -> None:
        """Set the complete owner identity used by subsequent account requests."""
        self._sfzmhm = value.strip().upper() if value else None

    async def async_authorize(self, authorization_code: str, ha_instance_id: str) -> dict[str, Any]:
        return await self._post(
            "/api/ha/authorize",
            {"authorization_code": authorization_code, "ha_instance_id": ha_instance_id},
            authenticated=False,
        )

    async def async_validate(self) -> dict[str, Any]:
        return await self._post("/api/ha/capabilities", {})

    async def async_login(self, *, device_id: str, data: str, mobile_session_id: str, token: str) -> dict[str, Any]:
        """Send capture fields and learn the complete identity returned by the relay."""
        payload = {
            "device_id": device_id,
            "data": data,
            "mobileSessionId": mobile_session_id,
            "token": token,
        }
        if self._sfzmhm:
            payload["sfzmhm"] = self._sfzmhm
        result = await self._post("/api/login", payload)
        data_block = result.get("data") if isinstance(result, dict) else None
        if isinstance(data_block, dict):
            # New relay versions expose the verified value as sfzmhm_full while
            # retaining the masked sfzmhm field for display compatibility.
            candidate = data_block.get("sfzmhm_full") or data_block.get("sfzmhm")
            if _valid_sfzmhm(candidate):
                self.set_sfzmhm(candidate)
        return result

    async def async_fetch_overview(self) -> dict[str, Any]:
        """Verify that the official account is actually usable after login."""
        return await self._post("/api/overview", self._account_payload())

    async def async_fetch_dashboard(self) -> dict[str, Any]:
        overview = await self.async_fetch_overview()
        violations = await self.async_fetch_violations()
        business_notices = await self.async_fetch_messages("2")
        service_reminders = await self.async_fetch_messages("1")
        return {
            "overview": overview.get("data", {}),
            "violations": violations,
            "business_notices": business_notices,
            "service_reminders": service_reminders,
        }

    async def async_fetch_violations(self) -> dict[str, Any]:
        """Fetch violation records and their official photo URLs."""
        return await self._post("/api/violations", self._account_payload())

    async def async_fetch_messages(self, category: str) -> dict[str, Any]:
        """Fetch one official message-center category for this account."""
        return await self._post("/api/messages", {**self._account_payload(), "xxlb": category})

    def _account_payload(self) -> dict[str, str]:
        """Return the identity required by the relay's account endpoints."""
        if not self._sfzmhm:
            raise JiaoguanAuthorizationError("缺少车主完整身份证号，请重新配置 12123 条目")
        return {"sfzmhm": self._sfzmhm}

    async def _post(self, path: str, payload: dict[str, Any], *, authenticated: bool = True) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if authenticated:
            if not self._access_token:
                raise JiaoguanAuthorizationError("缺少 Home Assistant 访问令牌")
            headers["Authorization"] = f"Bearer {self._access_token}"
        try:
            async with self._session.post(
                f"{self._base_url}{path}", json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=45),
            ) as response:
                try:
                    data = await response.json(content_type=None)
                except (aiohttp.ContentTypeError, ValueError) as err:
                    raise JiaoguanConnectionError("后端返回了非 JSON 响应") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise JiaoguanConnectionError(f"无法连接后端：{err}") from err

        message = data.get("message", "请求失败") if isinstance(data, dict) else "请求失败"
        if isinstance(data, dict) and (data.get("need_login") or (response.status == 404 and "登录" in message)):
            raise JiaoguanLoginRequiredError(message)
        if response.status in (401, 403, 409):
            raise JiaoguanAuthorizationError(message)
        if response.status >= 400 or not isinstance(data, dict) or data.get("code") not in (200, 201):
            raise JiaoguanApiError(message)
        return data


def _valid_sfzmhm(value: Any) -> bool:
    """Accept only an unmasked mainland 18-digit identity number."""
    return bool(re.fullmatch(
        r"[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])"
        r"(0[1-9]|[12]\d|3[01])\d{3}[\dX]",
        str(value or "").strip().upper(),
    ))
