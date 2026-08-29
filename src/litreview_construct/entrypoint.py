"""User-facing CLI entrypoint that registers all command extensions."""

from .app_cli import app
from . import plan_cli as _plan_cli  # noqa: F401  # command-registration side effect
from . import readiness_cli as _readiness_cli  # noqa: F401  # command-registration side effect
from . import navigator_cli as _navigator_cli  # noqa: F401  # command-registration side effect
from . import blueprint_cli as _blueprint_cli  # noqa: F401  # command-registration side effect
from . import ai_use_cli as _ai_use_cli  # noqa: F401  # command-registration side effect

__all__ = ["app"]
