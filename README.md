# Network Tools Dashboard

[![GitHub](https://img.shields.io/badge/repo-network--tools-informational)](https://github.com/dheerajnef-ai/network-tools)

Small **localhost** toolbox for DNS, HTTP probes, everyday shell-style checks (**host**, **dig**, **ping**, **nmap**, …), rough **geo** lookups (ipinfo), and **certificate** summaries.

Runs entirely on your machine—nothing here is a hosted service.

You get:

- **A browser UI** (**Flask + HTML**) at **http://127.0.0.1:5050** by default (**5050** sidesteps Apple’s occasional **AirPlay listener on 5000**.)
- **An optional companion script** that runs the **same Flask routes** behind the scenes when a **coding editor or terminal workflow** attaches to it—you can ignore that entire path if you only want the webpage.
- **`obsidian-notes/`** — three Markdown pages (**`START HERE.md`** opens first) meant for reading or pasting into **Obsidian**; symlink or copy the folder wherever you jot notes down.

Anything that shells out (**dig**, **nmap**, …) runs **on your machine** with your wiring. Treat it like any other probe kit and read **`INTERNAL-SETUP.txt`** before welcoming the wide internet.

Clone or pull: **[github.com/dheerajnef-ai/network-tools](https://github.com/dheerajnef-ai/network-tools)**

---

## First-time setup

```bash
cd network-tools-dashboard         # rename if you cloned elsewhere
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Optional extras** (`requirements-mcp.txt`) bundle the Flask stack **plus** the Python package the companion helper needs—install only when you intend to attach that helper.

```bash
pip install -r requirements-mcp.txt
```

Friendly-but-not-required binaries on **`PATH`**: **`dig`**, **`host`**, **`nslookup`**, **`ping` / `ping6`**, **`nmap`**.

---

## Run the web UI

Easiest:

```bash
chmod +x start.sh   # once per clone
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

Open **http://127.0.0.1:5050** (swap the port when you chose another).

---

## Notes beside Obsidian

Obsidian just reads Markdown from disk—you never have to cram the codebase into your vault.

| Everyday habit | Roughly |
|----------------|---------|
| Keep notes beside the checkout | Crack open **`obsidian-notes/`** from this repo. |
| Prefer them inside a vault folder | Copy the folder, or symlink—one example:  
`ln -s /full/path/to/.../obsidian-notes /full/path/to/your-vault/MyFolderName` |

Head note: **`START HERE.md`**. Stick to **that** doorway so you aren’t juggling two introductions.

Linked pages talk about routing names your editor advertises—you can skim or skip wholesale if browsers are all you touch.

---

## Optional editor helpers (hands-on hackers only)

If your editor understands **tiny JSON recipes** launching Python helpers beside a project folder, you can reuse the Flask logic without spawning the webpage every time:

1. Install **`requirements-mcp.txt`** (`pip`).
2. Open this repository as **the project root folder** inside your editor.
3. Start from **`editor-config/mcp-servers.example.json`** and merge that fragment into whichever file your toolchain expects beside the checkout (upstream docs spell the filenames). Keep private copies **out of git**—see **`.gitignore`** for dotted editor folders developers typically generate locally.
4. Flip the matching toggle in your editor’s **helper / toolchain** preferences (**wording hops between vendors and releases**).

**Stuck first boot?**

- Machine-specific JSON belongs in folders your editor designates; stray shell scribbles pasted into those manifests break parsers—keep chores in Markdown notes instead.
- The example points `python` at **`.venv/bin/python`** relative to **`${workspaceFolder}`** — keep the opened project root honest.

Rough idea of routed names (ignore completely if browsers cover your day):

| Routed name | What it feels like |
|-------------|---------------------|
| **network_lookup_smart** | Toss mixed inputs; guesses IP vs **`host:port`** vs hostname, then folds in optional shell chatter (`dig`, `all`, …). |
| **start_network_dashboard** | Same heartbeat as `./start.sh` whenever the webpage needs HTTP listening; quietly does nothing polite if anything already listens. |
| **domain_check** | Mirror of **Domain Check** tab logic. |
| **network_commands** | Mirror of **Network Commands** helpers (IPv6 gets gentler knobs when literals show up — see **`server.py`**). |
| **ip_geo_lookup** | Mirrors **IP Check** against ipinfo. |
| **ssl_certificate_inspect** | Mirrors **SSL** tab peeling; `:port` optional. |

Companion script: **`network_tools_mcp_server.py`**. Most routed calls never open a socket—Flask runs in-process for quick answers. Only the **start-…** style route truly revs the public listener when the browser complains about **Failed to fetch**.

---

## Layout (files worth knowing)

| Path | Purpose |
|------|---------|
| `server.py` | Flask API + glue behind the tabs |
| `index.html` | Browser layout |
| `network_tools_mcp_server.py` | Optional stdio buddy when editors wire it |
| `obsidian-notes/` | Loose notes + wikilinks |
| `INTERNAL-SETUP.txt` | Resolver flavor + safety language |
| `editor-config/mcp-servers.example.json` | Mergeable snippet for editor-hosted helper wiring |

---

## Why GitHub repeats one line beside many files?

GitHub shows **the commit that last touched that path**. Almost everything landed in **one giant commit**, so the website dutifully pastes **the same abbreviated title** on every touched row—not a glitch, just bookkeeping.

Send **smaller follow-up pushes** whenever you tweak different areas (“polish readme”, “adjust IPv6 command bundle”, …) and the table self-sorts again. Rows still quoting your **initial import** (`index.html`, `requirements.txt`, …) simply **never changed** since then—truthful, even if uneven.

Retroactive surgery (**rebase** + **force-push**) can rewrite captions for a lone maintainer vanity pass; ordinary teams leave history alone.

---

## One more reminder

Keep it localhost until you purposefully widen the blast radius. Peek **`INTERNAL-SETUP.txt`** when you’re tempted to punch through the firewall.
