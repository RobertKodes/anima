"""Hermes-class graphical CLI — banners, status, slash complete, command palette, overlays."""

from __future__ import annotations

from time import monotonic

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import Hit, Hits, Provider
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.widgets import Footer, Input as TextInput, RichLog, Static

from anima.app.commands import HELP, SLASH_PREFIXES
from anima.app.theme import BANNER, TUI_CSS
from anima.core.events import Reply, StreamPart
from anima.core.runtime import Runtime
from anima.development.metrics import snapshot


class SlashPalette(Provider):
    """Ctrl+P command palette over the same slash commands as the composer."""

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)
        app = self.app
        assert isinstance(app, AnimaApp)
        for name, summary in HELP:
            haystack = f"{name} {summary}"
            score = matcher.match(haystack)
            if score > 0:
                command = name.split("<")[0].split("...")[0].strip()
                yield Hit(
                    score,
                    matcher.highlight(name),
                    lambda line=command: app.submit_line(line),
                    help=summary,
                )


class HelpScreen(ModalScreen[None]):
    BINDINGS = [Binding("escape", "dismiss", "Close", show=True)]

    def compose(self) -> ComposeResult:
        lines = ["[#e8a04a b]commands[/]   esc to close", ""]
        for name, summary in HELP:
            lines.append(f"[#e8a04a]{name:<22}[/] {summary}")
        lines += [
            "",
            "[#8a7a68]tab completes  ·  ctrl+p palette  ·  F3 sleep  ·  ctrl+n new session[/]",
        ]
        yield Static("\n".join(lines), id="help-card")


class AnimaApp(App):
    CSS = TUI_CSS
    TITLE = "Anima"
    COMMANDS = {SlashPalette}
    BINDINGS = [
        Binding("ctrl+c", "quit", "Leave", show=True),
        Binding("ctrl+d", "quit", "Leave", show=False),
        Binding("ctrl+n", "new_session", "New session", show=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("f1", "show_help", "Help", show=True),
        Binding("f2", "slash_status", "Status", show=False),
        Binding("f3", "slash_sleep", "Sleep", show=True),
        Binding("f4", "slash_why", "Why", show=False),
    ]

    def __init__(self, runtime: Runtime) -> None:
        super().__init__()
        self.runtime = runtime
        self._started = monotonic()
        self._busy = "ready"
        self._stream_think = ""
        self._stream_reply = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="shell"):
            yield Static(id="banner")
            with Horizontal(id="body"):
                yield Static(id="side")
                with Vertical(id="chat-wrap"):
                    yield RichLog(id="chat", highlight=True, markup=True, wrap=True)
                    yield Static(id="stream")
                    yield Static(id="hints")
                    yield TextInput(
                        placeholder="Talk, or type /  —  tab completes  ·  ctrl+p palette",
                        id="composer",
                        suggester=SuggestFromList(SLASH_PREFIXES, case_sensitive=False),
                    )
                yield Static(id="why")
            yield Static(id="statusbar")
            yield Footer()

    def on_mount(self) -> None:
        self._refresh_chrome()
        boot = self.runtime.boot()
        log = self.query_one("#chat", RichLog)
        log.write("[#8a7a68]────────────────────────────────────────────[/]")
        if boot.birth:
            log.write("[#e8a04a]birth[/]  No persistent identity found.")
            log.write("[#8a7a68]hint[/]  Introduce yourself · try /skills · /fetch a URL when enabled")
        else:
            log.write("[#e8a04a]return[/]  A life is already underway in Sibyl.")
        for notice in boot.notices:
            log.write(f"[#8a7a68]{notice}[/]")
        self._write_being(boot)
        log.write("[#8a7a68]────────────────────────────────────────────[/]")
        self._refresh_chrome()
        self._refresh_why_text(
            "Birth is not a recalled life.\nThere is nothing to explain yet.\n\nTalk, then /why names the memories that mattered."
        )
        self.query_one("#composer", TextInput).focus()
        self.set_interval(0.2, self._tick)

    def on_input_changed(self, event: TextInput.Changed) -> None:
        if event.input.id != "composer":
            return
        self._update_hints(event.value)

    def on_input_submitted(self, event: TextInput.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        self._update_hints("")
        if not text:
            return
        self.submit_line(text)

    def submit_line(self, text: str) -> None:
        if self._busy != "ready":
            log = self.query_one("#chat", RichLog)
            log.write("[#8a7a68]…[/]  still composing the last reply")
            return
        log = self.query_one("#chat", RichLog)
        log.write(f"[#e8a04a]you[/]    {text}")
        self._stream_think = ""
        self._stream_reply = ""
        self._set_stream_visible(True)
        self._update_stream_panel()
        self._set_busy("remembering…")
        self._stream_reply_worker(text)

    @work(thread=True, exclusive=True)
    def _stream_reply_worker(self, text: str) -> None:
        final: Reply | None = None
        try:
            for part in self.runtime.iter_handle(text):
                self.call_from_thread(self._apply_stream_part, part)
                if part.kind == "done":
                    final = part.reply
        finally:
            self.call_from_thread(self._finish_stream, final)

    def _apply_stream_part(self, part: StreamPart) -> None:
        if part.kind == "status":
            self._set_busy(part.text)
            return
        if part.kind == "think":
            self._stream_think += part.text
            self._set_busy("thinking…")
        elif part.kind == "token":
            self._stream_reply += part.text
            self._set_busy("writing…")
        self._update_stream_panel()

    def _finish_stream(self, reply: Reply | None) -> None:
        self._set_stream_visible(False)
        if reply is not None:
            self._write_being(reply)
            self._refresh_chrome()
            self._refresh_why(reply)
            if reply.data.get("quit"):
                self.exit()
                return
        self._set_busy("ready")
        self.query_one("#composer", TextInput).focus()

    def _set_stream_visible(self, visible: bool) -> None:
        stream = self.query_one("#stream", Static)
        composer = self.query_one("#composer", TextInput)
        if visible:
            stream.add_class("active")
            composer.add_class("busy")
        else:
            stream.remove_class("active")
            composer.remove_class("busy")
            stream.update("")

    def _update_stream_panel(self) -> None:
        stream = self.query_one("#stream", Static)
        parts: list[str] = []
        if self._stream_think.strip():
            think = self._stream_think.strip()
            if len(think) > 900:
                think = "…" + think[-900:]
            parts.append(f"[#8a7a68 italic]thinking[/]  {think}")
        if self._stream_reply:
            parts.append(f"[#f4eadc]anima[/]  {self._stream_reply}[#8a7a68]▌[/]")
        elif not self._stream_think:
            parts.append("[#8a7a68]anima[/]  …")
        stream.update("\n".join(parts))

    def _set_busy(self, state: str) -> None:
        self._busy = state
        self._refresh_status()

    def action_new_session(self) -> None:
        self.submit_line("/new-session")

    def action_show_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_slash_status(self) -> None:
        self.submit_line("/status")

    def action_slash_sleep(self) -> None:
        self.submit_line("/sleep")

    def action_slash_why(self) -> None:
        self.submit_line("/why")

    def _write_being(self, reply: Reply) -> None:
        log = self.query_one("#chat", RichLog)
        for notice in reply.notices:
            log.write(f"[#7dba6a][{notice}][/]")
        for line in reply.text.splitlines() or [reply.text]:
            log.write(f"[#f4eadc]anima[/]  {line}")

    def _tick(self) -> None:
        if not self.is_running:
            return
        try:
            self._refresh_status()
        except Exception:
            return

    def _elapsed(self) -> str:
        seconds = int(monotonic() - self._started)
        minutes, sec = divmod(seconds, 60)
        return f"{minutes}m {sec:02d}s"

    def _refresh_chrome(self) -> None:
        data = self.runtime.status_data()
        mem = data["memory"]
        mem_line = "Sibyl connected" if mem.get("ok") else "Sibyl unavailable"
        if data["amnesia"]:
            mem_line = "Sibyl retrieval OFF (amnesia)"
        banner = self.query_one("#banner", Static)
        banner.update(
            BANNER
            + f"\n[#8a7a68]{mem_line}  ·  brain {data['primary']}  ·  Base {data['base'].get('network')}  ·  {data['stage']}[/]"
        )
        dev = snapshot(self.runtime.memory)
        evidence = dev.evidence
        people = []
        goals = []
        if self.runtime.memory.enabled:
            people = [
                ((row.get("body") or {}).get("name") or row.get("name"))
                for row in self.runtime.memory.list_entities("person", limit=6)
            ]
            goals = [
                ((row.get("body") or {}).get("title") or row.get("name"))
                for row in self.runtime.memory.list_entities("goal", limit=6)
            ]
        people_txt = "\n".join(f"  {name}" for name in people) or "  (none yet)"
        goals_txt = "\n".join(f"  {name}" for name in goals) or "  (none yet)"
        brains = "\n".join(_brain_line(row, data["primary"]) for row in data["brains"][:6])
        side = self.query_one("#side", Static)
        side.update(
            "[#e8a04a b]being[/]\n"
            f"stage   {dev.stage}\n"
            f"age     {dev.age_turns} turns\n"
            f"sleep   {dev.sleep_cycles}\n"
            f"life    {evidence.get('experiences', 0)} events\n"
            "\n[#e8a04a b]people[/]\n"
            f"{people_txt}\n"
            "\n[#e8a04a b]goals[/]\n"
            f"{goals_txt}\n"
            "\n[#e8a04a b]brains[/]\n"
            f"{brains}"
        )
        self._refresh_status()

    def _refresh_status(self) -> None:
        if not self.is_running:
            return
        data = self.runtime.status_data()
        mem = "sibyl" if data["memory"].get("ok") else "no-sibyl"
        try:
            bar = self.query_one("#statusbar", Static)
        except Exception:
            return
        bar.update(
            f" {self._busy}  ·  {data['primary']}  ·  {data['stage']}  ·  {data['age_turns']} turns  ·  {self._elapsed()}  ·  {mem}  ·  Base {data['base'].get('network')}"
        )

    def _refresh_why(self, reply: Reply) -> None:
        self._refresh_why_text(self.runtime.why().text)

    def _refresh_why_text(self, text: str) -> None:
        why = self.query_one("#why", Static)
        why.update("[#e8a04a b]why[/]\n" + (text or "No inspectable decision yet."))

    def _update_hints(self, value: str) -> None:
        hints = self.query_one("#hints", Static)
        if not value.startswith("/"):
            hints.update("")
            hints.remove_class("visible")
            return
        matches = [f"{name:<22} {summary}" for name, summary in HELP if name.startswith(value) or value[1:] in name]
        if not matches:
            matches = [f"{name:<22} {summary}" for name, summary in HELP]
        hints.update("[#e8a04a]commands[/]\n" + "\n".join(matches[:5]))
        hints.add_class("visible")


def _brain_line(row: dict, primary: str) -> str:
    mark = "*" if row.get("id") == primary else " "
    ok = "ok" if row.get("ok") else "down"
    return f"{mark} {row.get('id')} [{ok}]"


def run_tui(runtime: Runtime) -> None:
    AnimaApp(runtime).run()
