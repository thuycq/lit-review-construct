"""User-facing CLI entrypoint that registers all command extensions."""

from .app_cli import app
from . import plan_cli as _plan_cli  # noqa: F401  # command-registration side effect
from . import readiness_cli as _readiness_cli  # noqa: F401  # command-registration side effect

__all__ = ["app"]
