"""
httpcat - Discord bot
Copyright (C) 2020 - Saphielle Akiyama

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import asyncio
import random

from typing import Dict, List, Optional, Tuple, TypedDict, Union

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands.converter import clean_content

from config import CONFIG

# NOTE: This whole thing is made as a joke


class _ConfigOptional(TypedDict, total=False):
    intents: Dict[str, bool]


class Config(_ConfigOptional):
    token: str
    command_prefix: str
    support_server_url: str
    source_url: str


# fmt: off

VALID_CODES: List[int] = [
    100, 101, 102, 200, 201, 202, 203, 204, 
    206, 207, 300, 301, 302, 303, 304, 305,
    307, 308, 400, 401, 402, 403, 404, 405,
    406, 407, 408, 409, 410, 411, 412, 413, 
    414, 415, 416, 417, 418, 420, 421, 422,
    423, 424, 425, 426, 429, 431, 444, 450,
    451, 499, 500, 501, 502 ,503, 504, 506,
    507, 508, 509, 510, 511, 599,
]

# fmt: on


DEFAULT_INTENTS: Dict[str, bool] = {
    "guilds": True,
    "messages": True,
    "reactions": True,
}


class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        self.source_url = options.pop("source_url")

        self.__token = options.pop("token")
        os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
        self.load_extension("jishaku")

    async def connect(self, *args, **kwargs):
        """Dodging depreciation warnings"""
        self._session = aiohttp.ClientSession()
        return await super().connect(*args, **kwargs)

    @property
    def session(self) -> aiohttp.ClientSession:
        """Let's avoid accidentally re-assigning it"""
        return self._session

    def run(self, *args, **kwargs):
        """Accessing the config twice would be meh"""
        return super().run(self.__token, *args, **kwargs)

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Basic error handling"""
        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            msg = ctx.message
            assert msg is not None

            msg.content = f"http {msg.content}"
            return await bot.process_commands(msg)

        if isinstance(error, commands.CommandOnCooldown):
            cmd = ctx.command
            assert cmd is not None

            if cmd == "http":
                return
            elif cmd != "help" and error.retry_after < 3:

                await asyncio.sleep(error.retry_after)
                return await ctx.reinvoke()

        await ctx.send("{0.__class__.__name__}: {0}".format(error))
        return await super().on_command_error(ctx, error)

    async def close(self, *args, **kwargs):
        await self.session.close()
        return await super().close(*args, **kwargs)


class UsefulHelp(commands.HelpCommand):
    def get_command_signature(self, command: commands.Command) -> str:
        clean_prefix = clean_content

        if command.name == "http":
            return f"{self.context.prefix}{command.signature}"

        signature = "{0.context.prefix}{1.qualified_name} {1.signature}"
        return signature.format(self, command)

    async def send_embed(self, embed: discord.Embed) -> discord.Message:
        destination = self.get_destination()

        bot = self.context.bot
        invite_url = discord.utils.oauth_url(bot.user.id)

        links = [f"[Invite]({invite_url})", f"[Source]({bot.source_url})"]

        embed.add_field(name="Useful links", value=" | ".join(links))

        return await destination.send(embed=embed)

    async def send_all_help(self, *args, **kwargs):
        """Takes over all send_x_help that has multiple commands"""
        all_commands = [
            self.context.bot.get_command(command) for command in ("http", "random")
        ]

        embed = discord.Embed(title="Help")
        embed.color = discord.Color.from_hsv(
            random.random(), random.uniform(0.75, 0.95), 1
        )

        for command in all_commands:
            name = self.get_command_signature(command)
            embed.add_field(name=name, value=command.help, inline=False)

        return await self.send_embed(embed)

    send_bot_help = send_cog_help = send_group_help = send_all_help

    async def send_command_help(self, command: commands.Command):
        """Just one command"""
        embed = discord.Embed()
        embed.title = self.get_command_signature(command)
        embed.add_field(name="description", value=command.help)

        if aliases := "\n-".join(command.aliases):
            embed.add_field(name="aliases", value="-" + aliases)

        return await self.send_embed(embed)


intents = discord.Intents(**CONFIG.pop("intents", DEFAULT_INTENTS))
bot = Bot(**CONFIG, help_command=UsefulHelp(), intents=intents)  # type: ignore


def _parse_code(code: Optional[Union[int, str]] = None) -> int:
    if code is None:
        return 400
    try:
        code = int(code)
        if code in VALID_CODES:
            return code
        return 404
    except ValueError:
        return 422


@bot.command()
async def http(ctx: commands.Context, *, code: Optional[Union[int, str]] = None):
    """Shows the corresponding http cat image given a status code"""
    await ctx.send(f"https://http.cat/{_parse_code(code)}.jpg")


@bot.command(name="random")
async def random_(ctx: commands.Context):
    """Shows a random http cat"""
    code = random.choice(VALID_CODES)
    return await http(ctx, code=code)


@bot.slash_command(name="http")
async def _http(interaction: discord.Interaction, code: Optional[str] = None) -> None:
    """Shows the corresponding http cat image given a status code"""
    await interaction.response.send_message(f"https://http.cat/{_parse_code(code)}.jpg")


@bot.slash_command(name="http-random")
async def _http_random(interaction: discord.Interaction) -> None:
    """Shows a random http cat"""
    code = random.choice(VALID_CODES)
    await interaction.response.send_message(f"https://http.cat/{code}.jpg")


bot.run()
