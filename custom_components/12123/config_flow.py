"""Home Assistant config flow entry point."""

from .flow.authorization import ConfigFlow

__all__ = ["ConfigFlow"]
