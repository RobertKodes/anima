"""Local graphical companion. Same runtime, same Sibyl store. See docs/UI_PRD_v0.2.md."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from anima.core.runtime import Runtime

HTML = r"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anima</title>
<style>
  :root { --bg:#140f0a; --panel:#1e1610; --amber:#e8a04a; --text:#f4eadc; --muted:#8a7a68; --line:#3a2c20; --ok:#7dba6a; --warn:#d46a6a; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font: 15px/1.45 ui-sans-serif, system-ui, sans-serif; }
  header { padding:16px 24px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:baseline; }
  header strong { color:var(--amber); letter-spacing:.2em; }
  header span { color:var(--muted); font-size:13px; }
  main { display:grid; grid-template-columns: 240px minmax(0,1fr) 320px; min-height: calc(100vh - 56px); }
  aside, .rail { background:var(--panel); padding:16px 18px; overflow:auto; }
  aside { border-right:1px solid var(--line); }
  .rail { border-left:1px solid var(--line); }
  section { padding:16px 18px; display:flex; flex-direction:column; min-width:0; }
  h2 { font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:var(--amber); margin:18px 0 8px; }
  h2:first-child { margin-top:0; }
  .stat { color:var(--muted); margin:4px 0; }
  .stat b { color:var(--text); font-weight:600; }
  #log { flex:1; overflow:auto; }
  .msg { margin:0 0 12px; }
  .msg .who { color:var(--amber); font-size:11px; letter-spacing:.12em; text-transform:uppercase; }
  .notice { color:var(--ok); font-size:12px; }
  form { display:flex; gap:8px; margin-top:12px; }
  input { flex:1; background:#140f0a; color:var(--text); border:1px solid var(--amber); padding:11px 12px; border-radius:6px; }
  button { background:var(--amber); color:#140f0a; border:0; padding:11px 14px; border-radius:6px; font-weight:700; cursor:pointer; }
  pre, .item { white-space:pre-wrap; color:var(--muted); font: 12px/1.4 ui-monospace, Menlo, monospace; margin:0 0 8px; }
  .item { padding:8px; background:#140f0a; border:1px solid var(--line); border-radius:6px; }
</style>
<header>
  <strong>ANIMA</strong>
  <span>graphical companion · same Sibyl as the CLI · never a second being</span>
</header>
<main>
  <aside>
    <h2>Being</h2>
    <div id="status"></div>
    <h2>People</h2>
    <div id="people"></div>
    <h2>Goals</h2>
    <div id="goals"></div>
    <h2>Brains</h2>
    <div id="brains"></div>
    <h2>Base</h2>
    <div id="base"></div>
  </aside>
  <section>
    <div id="log"></div>
    <form id="f"><input id="q" autocomplete="off" placeholder="Talk, or type /help — memory lives in Sibyl"><button>Send</button></form>
  </section>
  <div class="rail">
    <h2>Why</h2>
    <pre id="why">No decision yet.</pre>
    <h2>Timeline</h2>
    <div id="timeline"></div>
    <h2>Last dream</h2>
    <pre id="dream">No sleep yet.</pre>
  </div>
</main>
<script>
const $ = id => document.getElementById(id);
function add(who, text, notice) {
  const div = document.createElement('div');
  div.className = 'msg';
  const safe = (text||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\n/g,'<br>');
  div.innerHTML = (notice ? `<div class="notice">[${notice}]</div>` : '') + `<div class="who">${who}</div><div>${safe}</div>`;
  $('log').appendChild(div); $('log').scrollTop = $('log').scrollHeight;
}
function items(id, rows, line) {
  $(id).innerHTML = (rows||[]).length ? rows.map(r => `<div class="item">${line(r)}</div>`).join('') : '<div class="stat">none yet</div>';
}
async function refresh() {
  const [s, life] = await Promise.all([
    fetch('/api/status').then(r => r.json()),
    fetch('/api/life').then(r => r.json()),
  ]);
  $('status').innerHTML = `
    <div class="stat">stage <b>${s.stage}</b></div>
    <div class="stat">age <b>${s.age_turns}</b> turns</div>
    <div class="stat">sleep <b>${s.sleep_cycles}</b></div>
    <div class="stat">sibyl <b>${s.memory.ok ? 'connected' : 'off'}</b></div>
    <div class="stat">amnesia <b>${s.amnesia}</b></div>`;
  items('people', life.people, p => (p.body&&p.body.name||p.name) + ' — ' + ((p.body&&p.body.summary)||''));
  items('goals', life.goals, g => '['+(g.body&&g.body.status||'')+'] ' + ((g.body&&g.body.title)||g.name));
  items('brains', s.brains, b => (b.id===s.primary?'* ':'  ') + b.id + ' ' + (b.ok?'ok':'down'));
  const b = s.base||{};
  $('base').innerHTML = `<div class="stat">${b.network} · ${b.approval_mode}</div>
    <div class="stat">dry-run <b>${b.dry_run}</b></div>
    <div class="stat">addr <b>${b.address||'none'}</b></div>`;
  items('timeline', life.events, e => (e.ts||'') + ' ' + JSON.stringify(e.acted));
  $('dream').textContent = (life.dream && (life.dream.report||life.dream.body&&life.dream.body.report)) || 'No sleep yet.';
}
$('f').onsubmit = async (e) => {
  e.preventDefault();
  const text = $('q').value.trim(); if (!text) return;
  add('you', text); $('q').value='';
  const r = await (await fetch('/api/chat', {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify({text})})).json();
  (r.notices||[]).forEach(n => add('notice', '', n));
  add('anima', r.text);
  $('why').textContent = r.why || '';
  refresh();
};
refresh();
fetch('/api/boot').then(r=>r.json()).then(r => { add('anima', r.text); refresh(); });
</script>
</html>
"""


def serve(runtime: Runtime, host: str = "127.0.0.1", port: int = 8787) -> int:
    boot = runtime.boot()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # noqa: A003
            return

        def _json(self, payload, code: int = 200) -> None:
            data = json.dumps(payload, default=str).encode()
            self.send_response(code)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/":
                body = HTML.encode()
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/status":
                self._json(runtime.status_data())
                return
            if path == "/api/boot":
                self._json({"text": boot.text, "notices": boot.notices, "birth": boot.birth})
                return
            if path == "/api/life":
                dream = runtime.memory.get_reference("last_dream")
                dream_body = None
                if dream:
                    dream_body = dream.get("body") if isinstance(dream.get("body"), dict) else dream
                self._json(
                    {
                        "people": runtime.memory.list_entities("person", limit=50),
                        "goals": runtime.memory.list_entities("goal", limit=50),
                        "events": runtime.memory.read_events(limit=20),
                        "onchain": runtime.memory.list_entities("onchain", limit=20),
                        "dream": dream_body,
                    }
                )
                return
            self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("content-length") or 0)
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode() or "{}")
            except json.JSONDecodeError:
                self._json({"error": "invalid JSON"}, 400)
                return
            text = str(payload.get("text") or "")
            reply = runtime.handle(text)
            why = runtime.why().text
            self._json({"text": reply.text, "notices": reply.notices, "why": why})

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Anima UI on http://{host}:{port}  (same Sibyl store as the CLI)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0
