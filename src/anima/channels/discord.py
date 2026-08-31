"""Discord bot — requires anima[discord] (discord.py)."""

from __future__ import annotations

from anima.channels.base import plain_reply
from anima.config.secrets import resolve_channel_token
from anima.core.runtime import Runtime


class DiscordChannel:
    name = "discord"

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.token = resolve_channel_token(runtime.cfg, "discord")
        if not self.token:
            raise RuntimeError(
                "Discord token missing. Set DISCORD_BOT_TOKEN or save to "
                f"{runtime.cfg.data_dir / 'secrets' / 'channels' / 'discord.json'}"
            )

    def run(self, runtime: Runtime) -> None:
        try:
            import discord
        except ImportError as exc:
            raise RuntimeError("pip install 'anima[discord]' to run the Discord channel") from exc

        runtime.boot()
        intents = discord.Intents.default()
        intents.message_content = True
        client = discord.Client(intents=intents)

        @client.event
        async def on_ready() -> None:
            print(f"[discord] logged in as {client.user} — Sibyl at {runtime.cfg.sibyl_db}")

        @client.event
        async def on_message(message: discord.Message) -> None:
            if message.author.bot:
                return
            if client.user not in message.mentions and not isinstance(message.channel, discord.DMChannel):
                return
            text = message.content
            for mention in message.mentions:
                text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
            text = text.strip()
            if not text:
                return
            reply = runtime.handle(text)
            await message.channel.send(plain_reply(reply)[:2000])

        client.run(self.token)
