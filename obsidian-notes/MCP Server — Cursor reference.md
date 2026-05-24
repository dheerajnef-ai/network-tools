# Cursor MCP — mellow reference

Keeps stride with [[00 Hub — Network Tools & MCP]] and [[Dashboard — Web UI]].

Think of MCP here as **headless dashboard buttons**. Cursor fires JSON at `network_tools_mcp_server.py`, which politely talks Flask on your behalf—you’re not juggling curl incantations manually.

Most calls never spin up Flask’s TCP listener—they lean on Flask’s **test harness** quietly. Spin up the listener only when Preview/fetch aches for it (**`start_network_dashboard`** MCP or `./start.sh`).

---

### Wire-up memory jog

Workspace root ought to equal the cloned repo (`…/network-tools-dashboard` naming optional).

Minimal **`.cursor/mcp.json`** (copy from **`mcp.json.example`**—the example ships in git; your personal **`mcp.json` typically stays gitignored**):

```json
{
  "mcpServers": {
    "network-tools-dashboard": {
      "command": "${workspaceFolder}/.venv/bin/python",
      "args": ["network_tools_mcp_server.py"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

Cursor settings → MCP → flick **network-tools-dashboard** on → reload Cursor if picky.

Separate warning: stray shell homework pasted inside **`~/.cursor/mcp.json`** poisons unrelated MCP integrations too—Markdown notes make better notebooks for commands.

Technical ID strings inside Cursor tooling may read longer (`project-0-…`). Human label remains **network-tools-dashboard**.

---

### What each knob does (plain names)

These names matter to Cursor—not your dinner guests:

| MCP tool | Loose translation |
|-----------|---------------------|
| **network_lookup_smart** | Toss mixed targets; it guesses IP vs **`host:port`** vs hostname. Optional **`extras_command`** tacks noisy shell summaries (`dig`, `all`, …). |
| **start_network_dashboard** | Background Flask process like `./start.sh`. Skips politely if localhost already chirps HTTP on that socket. **`open_browser`** optional. |
| **domain_check** | Domain tab logic. **`scope`** `external/internal`. |
| **network_commands** | Commands tab mimic. **`target`**, **`command`**, **`scope`**. IPv6 ergonomics mirrored from **`server.py`**. |
| **ip_geo_lookup** | IP tab mimic—ipinfo JSON. |
| **ssl_certificate_inspect** | TLS tab mimic; commas/lines okay; `:port` optional. |

---

### How **network_lookup_smart** sorts tokens

Rough mental shelf sort:

| You typed | Ends up routed through |
|-----------|---------------------------|
| Raw IPv4/IPv6 literal | **`/ip-lookup`** family |
| Token with `:port` (not “just IPv6 with colons”) | **`/ssl-check`** vibes |
| Hostname/domain | **`/check`** bundle |
| **`extras_command` ≠ none** | Also hits **`/network-command`** capped per codebase |

Internals shift when edge cases yell—read **`network_tools_mcp_server.py`** if you’re patching behavior.

---

### When you still flip `start_*` on?

| Feeling | MCP alone enough? |
|---------|-------------------|
| “Chat me DNS answers” during lunch | Yep—listeners optional |
| “I want real browser tabs humming” | **start_network_dashboard** or `./start.sh` |
| “Chrome says Failed to fetch” | HTTP server slept in—wake it |

---

### Friendly dependencies

```bash
pip install -r requirements-mcp.txt
```

Flask floats in courtesy of **`requirements.txt`**; MCP adds its Python package.

---

### Related files

**`network_tools_mcp_server.py`**, **`server.py`**, **`.cursor/mcp.json`** (personal), **`README.md`**.

---

[[00 Hub — Network Tools & MCP]] • [[Dashboard — Web UI]]
