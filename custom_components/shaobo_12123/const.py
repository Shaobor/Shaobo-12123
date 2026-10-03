"""Constants for the 12123 integration."""

import os
from typing import Final

DOMAIN: Final = "shaobo_12123"
PLATFORMS: Final = ["sensor"]
SERVICE_REFRESH_VIOLATIONS: Final = "refresh_violations"

CONF_AUTHORIZATION_CODE: Final = "authorization_code"
CONF_BACKEND_URL: Final = "backend_url"
CONF_ACCESS_TOKEN: Final = "access_token"
CONF_SFZMHM: Final = "sfzmhm"
CONF_SFZMHM_FULL: Final = "sfzmhm_full"
CONF_HA_INSTANCE_ID: Final = "ha_instance_id"
CONF_AUTHORIZATION_LABEL: Final = "authorization_label"
CONF_DEVICE_ID: Final = "device_id"
CONF_LOGIN_DATA: Final = "data"
CONF_MOBILE_SESSION_ID: Final = "mobileSessionId"
CONF_SSO_TOKEN: Final = "token"
CONF_SCAN_INTERVAL_MINUTES: Final = "scan_interval_minutes"
CONF_VIOLATION_SCAN_INTERVAL_MINUTES: Final = "violation_scan_interval_minutes"
CONF_MESSAGE_SCAN_INTERVAL_MINUTES: Final = "message_scan_interval_minutes"

DEFAULT_BACKEND_URL: Final = "https://traffic.hrbzlyy.com"
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 10
MIN_SCAN_INTERVAL_MINUTES: Final = 10
DEFAULT_VIOLATION_SCAN_INTERVAL_MINUTES: Final = 60
MIN_VIOLATION_SCAN_INTERVAL_MINUTES: Final = 10
MIN_MESSAGE_SCAN_INTERVAL_MINUTES: Final = 10
