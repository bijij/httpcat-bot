from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import Config

CONFIG: Config = {
    "token": "discord-token",
    "command_prefix": "!",
    "support_server_url": "url",
    "source_url": "url",
    "fetch_offline_members": False,
    "guild_subscriptions": False,
}
