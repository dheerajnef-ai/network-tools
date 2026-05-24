# Network Tools Dashboard

[![GitHub](https://img.shields.io/badge/repo-network--tools-informational)](https://github.com/dheerajnef-ai/network-tools)

Small **localhost** toolbox for DNS, HTTP probes, everyday shell-style checks (**host**, **dig**, **ping**, **nmap**, …), rough **geo** lookups (ipinfo), and **certificate** summaries. Ships with a plain **Flask + HTML** UI and optional **Cursor MCP** bindings if you already use Cursor.

Clone or download: **[github.com/dheerajnef-ai/network-tools](https://github.com/dheerajnef-ai/network-tools)**

---

## What you actually get

- **Browser tabs** at **http://127.0.0.1:5050** (default port—change with `PORT=…`; **5050** sidesteps Apple’s occasional **AirPlay listener on 5000**.)
- Same logic callable from **Cursor** as MCP tools (see below)—handy when you’d rather chat than click.
- **`obsidian-notes/`** — a short **Markdown** cheat sheet trio you can paste or symlink into an **Obsidian** vault—your notes stay yours; this repo stays code.

Anything that shells out (**dig**, **nmap**, etc.) obviously runs **on your machine** with your network path. Treat it like any other diagnostic tool; see **`INTERNAL-SETUP.txt`** before exposing it past **localhost**.

---

## First-time setup

```bash
cd network-tools-dashboard   # or whatever you cloned it as
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

Optional MCP support (pulls Flask + MCP SDK):

```bash
pip install -r requirements-mcp.txt
```

Helpful-but-not-required on **PATH**: `dig`, `host`, `nslookup`, `ping` / `ping6`, `nmap`.

---

## Run the web UI

Easiest:

```bash
chmod +x start.sh   # once
./start.sh
```

Or:

```bash
source .venv/bin/activate
python server.py
```

Another port:

```bash
PORT=8080 python server.py
```

Then open **http://127.0.0.1:5050** (adjust port if you changed it).

---

## Obsidian vault (human notes beside the repo)

Obsidian reads **Markdown on disk**. You don’t have to cram the codebase into your vault—a **symlink** or a **copied folder** works fine.

- **Packaged cheatsheets**: folder **`obsidian-notes/`** in this repo (hub + MCP page + dashboard page, with normal Obsidian **`[[wikilinks]]`** between them).
- **Short pointer**: root file **`Obsidian-Network-Tools-Dashboard.md`**.

Pick what fits you:

| Idea | Roughly |
|------|--------|
| Notes live only in Cursor | Browse `obsidian-notes/` here. |
| Notes live in Obsidian | Copy **`obsidian-notes/`** somewhere under your vault, **or** `ln -s /full/path/to/.../obsidian-notes /full/path/to/yourVault/AnyFolderName`. Then open the hub note from that folder in Obsidian. |

Edits in either app hit the **same markdown files** if you symlink—as soon as Obsidian refreshes its view.

---

## Cursor MCP (optional)

Wire-up is boring on purpose:

1. Use the **`pip install`** line above (`requirements-mcp.txt`).
2. Open **this repo** as Cursor’s workspace root (`File → Open Folder…`).
3. Copy **`.cursor/mcp.json.example`** → **`.cursor/mcp.json`** (template only lives in repo; **`mcp.json` itself is gitignored**—keep your local copy.)
4. **Settings → Tools & MCP** → enable **`network-tools-dashboard`**.

If something flakes out, **`View → Output → MCP`** is the sensible first stop. Broken JSON in **`~/.cursor/mcp.json`** tends to confuse *every* MCP entry—stash shell snippets in Markdown, not in that file.

Rough idea of each tool (**names are for Cursor/automation—you can ignore these if you only use the website**):

| Name | Layperson version |
|------|---------------------|
| **network_lookup_smart** | Figures out IPs vs domains vs **`host:port`** and routes to the right check. Optional extra shell bundles (`dig`, `all`, …). |
| **start_network_dashboard** | Spins up the actual HTTP server like `./start.sh` when the browser tabs need **`fetch`** to succeed. Skips itself if something already answers that port. |
| **domain_check** | Same bundle as **Domain Check** in the UI. |
| **network_commands** | **Network Commands** tab (dig / ping / …). IPv6 literals get friendlier tooling where we could wire it (**ping6**, **nmap -6**, PTR **dig**, etc.—see **`server.py`**). |
| **ip_geo_lookup** | Lookup against ipinfo-style JSON (**IP Check** tab). |
| **ssl_certificate_inspect** | PEM-ish summary (**SSL** tab); optional **`:port`**. |

Most MCP calls don’t *need* the browser server—only the **`start_*`** helper does—because Flask is invoked internally. That’s deliberate so “quick lookup in chat” stays lightweight.

---

## Layout (files worth knowing)

| Path | Purpose |
|------|---------|
| `server.py` | Flask API + orchestration behind the tabs |
| `index.html` | Browser UI |
| `network_tools_mcp_server.py` | MCP sidecar for Cursor |
| `obsidian-notes/` | Human-readable docs for Obsidian (or Cursor) |
| `INTERNAL-SETUP.txt` | Internal vs external DNS notes, tighter security wording |
| `.cursor/mcp.json.example` | Paste → `mcp.json` locally |

---

## One more reminder

Use it on localhost until you intentionally deploy it. Read **`INTERNAL-SETUP.txt`** when you leave your happy path.
